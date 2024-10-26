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
                logger.info("登录成功,发送成功通知邮件...")
                notify_success(
                    f"登录成功URL:{page_titles['url']}\n"
                    f"登录页面标题: {page_titles['login']}\n"
                    f"登录后页面标题: {page_titles['after_login']}"
                )
            else:
                logger.error("登录失败，已达到最大重试次数")
                notify_failure(
                    f"登录失败, 详情:\n"
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

def validate_env_vars():
    required_vars = ['WEBSITE_URL', 'USERNAME', 'PASSWORD', 'MAX_RETRIES', 
                     'LOGIN_SCHEDULE_TYPE', 'LOGIN_SCHEDULE_DATE', 'LOGIN_SCHEDULE_TIME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")
    # TODO 检查配置项的值合法性

def main():
    try:
        validate_env_vars()

        auto_login = AutoLogin()
        login_schedule_type = os.getenv('LOGIN_SCHEDULE_TYPE')
        login_schedule_date = os.getenv('LOGIN_SCHEDULE_DATE')
        login_schedule_time = os.getenv('LOGIN_SCHEDULE_TIME')
        retry_interval = 1

        if login_schedule_type == 'monthly':
            if not login_schedule_date.isdigit() or not (1 <= int(login_schedule_date) <= 31):
                raise ValueError("LOGIN_SCHEDULE_DATE 必须是1到31之间的数字")
            logger.info(f"每月 {login_schedule_date} 号 {login_schedule_time} 时自动进行登录...")
            schedule.every().month.on(int(login_schedule_date)).at(login_schedule_time).do(auto_login.attempt_login)
            retry_interval = 60 * 24
        elif login_schedule_type == 'minutes':
            logger.info("测试 - 使用分钟级调度, 每分钟登录一次...")
            schedule.every(retry_interval).minutes.do(auto_login.attempt_login)
            # 启动时运行一次
            auto_login.attempt_login()
        else:
            raise ValueError(f"无效的LOGIN_SCHEDULE_TYPE: {login_schedule_type}")

        # 保持调度器运行
        while True:
            schedule.run_pending()
            time.sleep(retry_interval * 60)

    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        notify_failure(f"自动登录调度任务异常: {e}")

if __name__ == "__main__":
    main()
