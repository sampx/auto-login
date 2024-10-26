from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)
# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

class BrowserHandler:
    def __init__(self):
        """初始化浏览器处理类"""
        self.browser = None  # 浏览器实例
        self.context = None  # 浏览器上下文
        self.page = None  # 页面实例
        self.playwright = None  # Playwright实例

    def setup_browser(self):
        """设置浏览器"""
        try:
            logger.info("正在设置浏览器...")
            self.playwright = sync_playwright().start()  # 启动Playwright
            self.browser = self.playwright.chromium.launch(
                headless=True,  # 无头模式
                args=['--no-sandbox', '--disable-setuid-sandbox']  # 启动参数
            )
            # 设置浏览器上下文，包括语言设置
            self.context = self.browser.new_context(
                locale='en-US',  # 设置为英语
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',  # 请求英语内容
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            self.page = self.context.new_page()  # 创建新页面
            logger.info("浏览器设置完成")
        except Exception as e:
            logger.error(f"设置浏览器失败: {str(e)}")
            self.cleanup()  # 清理资源
            raise

    def get_page_html(self):
        """获取页面HTML内容"""
        logger.info("正在获取页面HTML内容...")
        try:
            html_content = self.page.content()
            logger.debug("页面HTML内容:")
            logger.debug(html_content)
            return html_content
        except Exception as e:
            logger.error(f"获取页面HTML失败: {str(e)}")
            return None

    def get_page_info(self):
        """获取页面信息，包括标题和响应头"""
        logger.info("正在获取页面表单和标题信息...")
        try:
            info = self.page.evaluate('''() => {
                const titleElement = document.querySelector('title');
                const forms = Array.from(document.forms).map(form => ({
                    id: form.id,
                    action: form.action,
                    method: form.method,
                    innerHTML: form.innerHTML
                }));
                const inputs = Array.from(document.querySelectorAll('input')).map(input => ({
                    type: input.type,
                    name: input.name,
                    id: input.id,
                    value: input.type !== 'password' ? input.value : '***'
                }));
                return {
                    title: titleElement ? titleElement.textContent : '',
                    url: window.location.href,
                    forms: forms,
                    inputs: inputs
                };
            }''')
            
            logger.debug(f"页面信息 - 标题: {info['title']}")
            logger.debug(f"页面信息 - URL: {info['url']}")
            logger.debug("表单信息:")
            for form in info['forms']:
                logger.debug(f"  表单: id={form['id']}, action={form['action']}, method={form['method']}")
            logger.debug("输入框信息:")
            for input_field in info['inputs']:
                logger.debug(f"  输入框: type={input_field['type']}, name={input_field['name']}, id={input_field['id']}, value={input_field['value']}")
            
            return info['title']
        except Exception as e:
            logger.error(f"获取页面信息失败: {str(e)}")
            return None

    def analyze_page(self):
        """分析页面内容，帮助调试"""
        try:
            # 获取所有按钮元素
            buttons = self.page.query_selector_all('button[type="submit"]')
            logger.debug(f"页面中找到 {len(buttons)} 个提交按钮")
            for button in buttons:
                text = button.evaluate('node => node.textContent')
                logger.debug(f"按钮文本: {text}, id: {button.get_attribute('id')}, type: {button.get_attribute('type')}")

            # 获取所有表单元素
            forms = self.page.query_selector_all('form')
            logger.debug(f"页面中找到 {len(forms)} 个表单")
            for form in forms:
                logger.debug(f"表单action: {form.get_attribute('action')}, method: {form.get_attribute('method')}")
                logger.debug(f"表单HTML: {form.inner_html()}")

            # 检查是否有错误信息显示
            error_elements = self.page.query_selector_all('.alert-error, .alert-danger, .error-message')
            for error in error_elements:
                text = error.evaluate('node => node.textContent')
                logger.debug(f"发现错误信息: {text}")

        except Exception as e:
            logger.error(f"分析页面失败: {str(e)}")

    def check_login_status(self):
        """检查登录状态并获取详细信息"""
        try:
            # 检查URL
            current_url = self.page.url
            logger.debug(f"当前URL: {current_url}")
            
            # 检查页面上的错误信息
            error_info = self.page.evaluate('''() => {
                const errors = [];
                // 检查常见的错误消息容器
                const errorSelectors = [
                    '.alert-error', '.alert-danger', '.error-message',
                    '#error-message', '.form-error', '.login-error'
                ];
                
                for (const selector of errorSelectors) {
                    const element = document.querySelector(selector);
                    if (element && element.textContent.trim()) {
                        errors.push(element.textContent.trim());
                    }
                }
                
                // 检查表单验证消息
                const invalidInputs = document.querySelectorAll('input:invalid');
                invalidInputs.forEach(input => {
                    if (input.validationMessage) {
                        errors.push(`${input.name}: ${input.validationMessage}`);
                    }
                });
                
                return {
                    url: window.location.href,
                    errors: errors,
                    isLoginPage: window.location.href.includes('/login/')
                };
            }''')
            
            logger.debug(f"登录状态检查结果: {error_info}")
            return error_info
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {str(e)}")
            return None

    def login(self, url, username, password, max_retries):
        """登录操作"""
        if not self.page:
            self.setup_browser()  # 如果页面未初始化，先设置浏览器
            
        retry_count = 0
        page_titles = {'login': None, 'after_login': None}  # 存储登录前后的页面标题
        
        while retry_count < max_retries:
            try:
                logger.info(f"尝试第 {retry_count + 1} 次，共 {max_retries} 次")
                
                # 导航到登录页面，设置较长的超时时间
                logger.info(f"登录到URL: {url}")
                response = self.page.goto(url, timeout=60000, wait_until='networkidle')
                if not response:
                    raise Exception("页面加载失败")
                if response.status >= 400:  # 只有状态码大于等于400才是错误
                    raise Exception(f"页面加载失败，状态码: {response.status}")
                
                logger.debug(f"页面加载成功，状态码: {response.status}")
                
                # 获取页面HTML内容
                html_content = self.get_page_html()
                if not html_content:
                    raise Exception("无法获取页面HTML内容")
                
                # 获取登录页面标题和信息
                page_titles['login'] = self.get_page_info()
                
                # 分析页面结构
                self.analyze_page()
                
                # 等待用户名输入框
                logger.debug("等待用户名输入框...")
                username_field = self.page.wait_for_selector('#id_username', timeout=5000)
                if not username_field:
                    raise Exception("未找到用户名输入框")
                
                # 等待密码输入框
                logger.debug("等待密码输入框...")
                password_field = self.page.wait_for_selector('#id_password', timeout=5000)
                if not password_field:
                    raise Exception("未找到密码输入框")
                
                # 填写用户名和密码
                logger.debug("填写用户名和密码...")
                username_field.fill(username)
                password_field.fill(password)
                
                # 等待提交按钮
                logger.debug("等待提交按钮...")
                submit_button = self.page.wait_for_selector('#submit', timeout=5000)
                if not submit_button:
                    raise Exception("未找到提交按钮")
                
                # 等待网络请求完成
                logger.debug("点击提交按钮...")
                with self.page.expect_navigation(timeout=60000, wait_until='networkidle'):
                    submit_button.click()
                
                # 获取登录后页面标题
                page_titles['after_login'] = self.get_page_info()
                
                # 检查登录状态
                login_status = self.check_login_status()
                
                if login_status:
                    if not login_status['isLoginPage']:
                        logger.info("登录成功 - 已离开登录页面")
                        return True, page_titles
                    elif login_status['errors']:
                        error_message = '; '.join(login_status['errors'])
                        raise Exception(f"登录失败: {error_message}")
                    else:
                        # 检查是否有任何错误提示
                        error_text = self.page.evaluate('''() => {
                            const errorElements = document.querySelectorAll('.alert, .error, .alert-error, .alert-danger');
                            for (const el of errorElements) {
                                if (el.textContent.trim()) {
                                    return el.textContent.trim();
                                }
                            }
                            return null;
                        }''')
                        if error_text:
                            raise Exception(f"登录失败: {error_text}")
                        else:
                            raise Exception("登录失败: 仍在登录页面但未发现具体错误信息")
                
            except PlaywrightTimeoutError as e:
                logger.error(f"登录尝试超时: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"等待5秒后重试...")
                    time.sleep(5)
                
            except Exception as e:
                logger.error(f"登录尝试失败: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"等待5秒后重试...")
                    time.sleep(5)
        
        return False, page_titles

    def cleanup(self):
        """清理浏览器资源"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("浏览器资源清理成功")
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")
