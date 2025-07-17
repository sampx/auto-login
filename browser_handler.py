import os
import signal
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time

class BrowserHandler:
    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        else:
            from logger_helper import LoggerHelper
            # 默认使用系统日志记录器
            self.logger = LoggerHelper.get_system_logger("browser_handler")  
        self.browser = None  # 浏览器实例
        self.context = None  # 浏览器上下文
        self.page = None  # 页面实例
        self.playwright = None  # Playwright实例

    def setup_browser(self):
        """设置浏览器"""
        try:
            self.logger.info("正在设置浏览器...")
            self.playwright = sync_playwright().start()  # 启动Playwright
            self.browser = self.playwright.chromium.launch(
                headless=True,  # 无头模式
                args=['--no-sandbox', '--disable-setuid-sandbox']  # 启动参数
            )
            # 设置浏览器上下文，包括语言设置
            self.logger.debug("设置浏览器语言环境为英语")
            self.context = self.browser.new_context(
                locale='en-US',  # 设置为英语
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',  # 请求英语内容
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            self.page = self.context.new_page()  # 创建新页面
            self.logger.info("浏览器设置完成")
        except Exception as e:
            self.logger.error(f"设置浏览器失败: {str(e)}")
            self.cleanup()  # 清理资源
            raise

    def open_login_page(self, login_url):
        """进行登录"""
        self.logger.debug(f"导航到登录页:{login_url}...")
        try:
            response = self.page.goto(login_url, timeout=60000, wait_until='networkidle')
            if not response:
                raise Exception("页面加载失败: 无响应")
            if response.status >= 400:
                raise Exception(f"页面加载失败, 错误响应码: {response.status}")
            self.logger.debug(f"成功加载登录页面, 状态码: {response.status}")
        except PlaywrightTimeoutError as e:
            self.logger.error(f"页面加载超时: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"登录页面加载过程中出现错误: {str(e)}")
            raise

    def get_page_info(self):
        """获取页面信息，包括标题和响应头"""        
        try:            
            info = self.page.evaluate('''() => {
                const titleElement = document.querySelector('title');
                return {
                    title: titleElement ? titleElement.textContent : 'not found',
                    url: window.location.href
                };
            }''')
            
            self.logger.debug(f"页面标题: {info['title']}, 页面URL: {info['url']}")            
            return info['title']
        except Exception as e:
            self.logger.error(f"获取页面信息失败: {str(e)}")
            return None
    def gather_login_elements(self):
        """获取页面HTML、页面信息, 并查找登录相关的元素"""        
        try:
            html_content = self.page.content()
            self.logger.debug(f"页面HTML内容:\n{str(html_content)}")   
            # TODO 优化此处适应大多数网站的登录元素查找逻辑
            # 获取页面信息
            # info = self.page.evaluate('''() => {                
            #     const forms = Array.from(document.forms).map(form => ({
            #         id: form.id,
            #         action: form.action,
            #         method: form.method,
            #         innerHTML: form.innerHTML
            #     }));
            #     const inputs = Array.from(document.querySelectorAll('input')).map(input => ({
            #         type: input.type,
            #         name: input.name,
            #         id: input.id,
            #         value: input.type !== 'password' ? input.value : '***'
            #     }));
            #     const buttons = Array.from(document.querySelectorAll('button[type="submit"]')).map(button => ({
            #         type: button.type,
            #         name: button.name,
            #         id: button.id
            #     }));
            #     return {
            #         forms: forms,
            #         inputs: inputs,
            #         buttons: buttons
            #     };
            # }''')
            
            # # 打印info调试信息
            # self.logger.debug(f"表单数量: {len(info['forms'])}")
            # for form in info['forms']:
            #     self.logger.debug(f"表单ID: {form['id']}, 动作: {form['action']}, 方法: {form['method']}")
            #     self.logger.debug(f"表单HTML: {form['innerHTML']}")
            # self.logger.debug(f"输入字段数量: {len(info['inputs'])}")
            # for input_field in info['inputs']:
            #     self.logger.debug(f"字段类型: {input_field['type']}, 名称: {input_field['name']}, 值: {input_field['value']}, id: {input_field['id']}")  
            # self.logger.debug(f"按钮数量: {len(info['buttons'])}")
            # for button in info['buttons']:
            #     self.logger.debug(f"按钮类型: {button['type']}, 名称: {button['name']}, id: {button['id']}")
            

            # 获取所有按钮元素
            # buttons = self.page.query_selector_all('button[type="submit"]')
            # self.logger.debug(f"页面中找到 {len(buttons)} 个提交按钮")
            # for button in buttons:
            #     text = button.evaluate('node => node.textContent')
            #     self.logger.debug(f"按钮文本: {text}, id: {button.get_attribute('id')}, type: {button.get_attribute('type')}")

            # 获取所有表单元素
            # forms = self.page.query_selector_all('form')
            # self.logger.debug(f"页面中找到 {len(forms)} 个表单")
            # for form in forms:
            #     self.logger.debug(f"表单action: {form.get_attribute('action')}, method: {form.get_attribute('method')}")
            #     self.logger.debug(f"表单HTML: {form.inner_html()}")

            # 检查是否有错误信息显示
            # error_elements = self.page.query_selector_all('.alert-error, .alert-danger, .error-message')
            # for error in error_elements:
            #     text = error.evaluate('node => node.textContent')
            #     self.logger.debug(f"发现错误信息: {text}")

            # 查询用户名和密码输入框，以及提交按钮
            username_field = self.page.query_selector('#id_username')
            password_field = self.page.query_selector('#id_password')
            submit_button = self.page.query_selector('#submit')

            # 等待用户名输入框
            # self.logger.debug("等待用户名输入框...")
            # username_field = self.page.wait_for_selector('#id_username', timeout=5000)
            # if not username_field:
            #     raise Exception("未找到用户名输入框")
            
            # 等待密码输入框
            # self.logger.debug("等待密码输入框...")
            # password_field = self.page.wait_for_selector('#id_password', timeout=5000)
            # if not password_field:
            #     raise Exception("未找到密码输入框")
            
            # 等待提交按钮
            # self.logger.debug("等待提交按钮...")
            # submit_button = self.page.wait_for_selector('#submit', timeout=5000)
            # if not submit_button:
            #     raise Exception("未找到提交按钮")

            if not username_field or not password_field or not submit_button:
                raise Exception("未找到登录所需的元素")

            return username_field, password_field, submit_button

        except Exception as e:
            self.logger.error(f"获取登录元素失败: {str(e)}")
            return None, None, None, None
   
    def check_login_status(self):
        """检查登录状态并获取详细信息"""
        try:
            # 获取当前 URL
            current_url = self.page.url  

            self.logger.info(f"检查登录状态: 当前页面: {current_url}")

            # 执行 JavaScript 以获取错误信息和登录状态
            error_info = self.page.evaluate('''() => {
                const errors = [];
                // 常见的错误消息选择器
                const errorSelectors = [
                    '.error', '.error-message', '#error-message',
                    '.form-error', '.login-error','.login-error-message',
                    '.alert', '.alert-error', '.alert-danger'
                ];

                // 检查页面上的错误消息
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
                    errors: errors
                };
            }''')

            # 记录错误检查的结果
            if error_info['errors']:
                self.logger.error(f"页面错误信息: {error_info['errors']}")
            else:
                self.logger.debug("页面未发现错误信息")

            # 添加 URL 信息到结果中
            error_info['url'] = current_url
            error_info['isLoginPage'] = '/login/' in current_url

            return error_info

        except Exception as e:
            self.logger.error(f"检查登录状态失败: {str(e)}")
            return {
                'url': current_url,
                'errors': [str(e)],
                'isLoginPage': '/login/' in current_url
            }


    def login(self, url, username, password, max_retries):
        """登录操作"""
        if not self.page:
            self.setup_browser()  # 如果页面未初始化，先设置浏览器
            
        retry_count = 0
        page_titles = {'login': None, 'after_login': None}  # 存储登录前后的页面标题
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"尝试第 {retry_count + 1} 次，共 {max_retries} 次")
                
                # 导航到登录页面，设置较长的超时时间
                self.logger.info(f"登录到URL: {url}")
                self.page.set_default_timeout(60000)

                # 打开登录页面
                self.logger.info("打开登录页面...")
                self.open_login_page(url)  

                # 获取登录页面标题和信息
                page_titles['login'] = self.get_page_info()
                
                # 获取页面输入元素
                self.logger.info("查找登录元素...")
                username_field, password_field, submit_button = self.gather_login_elements()
                
                # 填写用户名和密码
                self.logger.info("填写用户名和密码...")
                username_field.fill(username)
                password_field.fill(password)                
                
                # 等待网络请求完成
                self.logger.info("点击提交按钮...")
                with self.page.expect_navigation(timeout=60000, wait_until='networkidle'):
                    submit_button.click()
                
                # 检查登录状态
                self.logger.info("检查登录状态...")
                login_status = self.check_login_status()

                if login_status['errors']:
                    error_message = '; '.join(login_status['errors'])
                    # 忽略错误信息
                    # raise Exception(f"登录失败: {error_message}")       
                
                # 获取登录后页面标题
                self.logger.info("页面加载完成,获取登录后页面标题...")
                page_titles['after_login'] = self.get_page_info()
                page_titles['url'] = login_status['url']

                if not login_status['isLoginPage']:
                    self.logger.info("登录成功 - 已离开登录页面")
                    return True, page_titles
                                
            except PlaywrightTimeoutError as e:
                self.logger.error(f"登录尝试超时: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"等待5秒后重试...")
                    time.sleep(5)                
            except Exception as e:
                self.logger.error(f"登录尝试失败: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"等待5秒后重试...")
                    time.sleep(5)
        
        return False, page_titles

    def cleanup(self):
        """清理浏览器资源"""
        try:
            self.logger.info("开始清理浏览器资源...")
            cleanup_timeout = 10  # 设置清理超时时间为10秒
            
            def force_exit():
                self.logger.warning("清理超时,强制退出...")
                os.kill(os.getpid(), signal.SIGKILL)
            
            # 启动超时计时器
            timer = threading.Timer(cleanup_timeout, force_exit)
            timer.start()
            
            try:
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
                self.logger.info("浏览器资源清理成功")
            finally:
                # 取消计时器
                timer.cancel()
                
        except Exception as e:
            self.logger.error(f"清理资源时出错: {str(e)}")
            # 如果清理过程出错,也强制退出
            os.kill(os.getpid(), signal.SIGKILL)
