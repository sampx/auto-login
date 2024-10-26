import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from browser_handler import BrowserHandler
from email_notifier import notify_success, notify_failure
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class AutoLogin:
    def __init__(self):
        self.url = os.getenv('WEBSITE_URL')  # 获取网站URL
        self.username = os.getenv('USERNAME')  # 获取用户名
        self.password = os.getenv('PASSWORD')  # 获取密码
        self.max_retries = int(os.getenv('MAX_RETRIES')) # 最大重试次数
        self.browser_handler = None  # 浏览器处理对象

    def attempt_login(self):
        try:
            logger.info(f"开始登录尝试，时间: {datetime.now()}")
            
            # 初始化浏览器处理对象
            self.browser_handler = BrowserHandler()
            
            # 执行登录操作
            success, page_titles = self.browser_handler.login(
                self.url,
                self.username,
                self.password,
                self.max_retries
            )

            if success:
                logger.info("登录成功")
                notify_success(
                    f"登录页面标题: {page_titles['login']}\n"
                    f"登录后页面标题: {page_titles['after_login']}"
                )
            else:
                logger.error("登录失败，已达到最大重试次数")
                notify_failure(
                    f"登录失败详情:\n"
                    f"- 尝试次数: {self.max_retries}\n"
                    f"- 目标网站: {self.url}\n"
                    f"- 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

        except Exception as e:
            error_msg = (
                f"登录尝试过程中发生错误:\n"
                f"- 错误类型: {type(e).__name__}\n"
                f"- 错误信息: {str(e)}\n"
                f"- 发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"- 目标网站: {self.url}"
            )
            logger.error(error_msg)
            notify_failure(error_msg)
        finally:
            if self.browser_handler:
                self.browser_handler.cleanup()

def main():
    auto_login = AutoLogin()
    
    # 安排登录尝试
    # schedule.every().day.at("09:00").do(auto_login.attempt_login)
    schedule.every(1).minutes.do(auto_login.attempt_login)
    
    # 启动时立即运行一次
    auto_login.attempt_login()
    
    # 保持调度器运行
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
