import os
import time
import signal
import sys
from datetime import datetime
from dotenv import load_dotenv
from browser_handler import BrowserHandler
from email_notifier import notify_success, notify_failure
import logging
import re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# 加载环境变量
load_dotenv()
# 全局变量
scheduler = None
browser_handler = None

class AutoLogin:
    def __init__(self):
        from logger_helper import LoggerHelper
        # 使用任务日志记录器 - 只记录到任务日志文件
        self.logger = LoggerHelper.get_task_logger("auto_login")
        self.url = os.getenv('WEBSITE_URL')  # 获取网站URL
        self.username = os.getenv('USERNAME')  # 获取用户名
        self.password = os.getenv('PASSWORD')  # 获取密码
        self.max_retries = int(os.getenv('MAX_RETRIES')) # 最大重试次数
        self.browser_handler = None  # 浏览器处理对象

    def attempt_login(self):
        try:
            self.logger.info(f"开始登录尝试，时间: {datetime.now()}")
            
            # 初始化浏览器处理对象,并传入任务日志记录器
            self.browser_handler = BrowserHandler(logger=self.logger)
            global browser_handler
            browser_handler = self.browser_handler
            
            # 执行登录操作
            success, page_titles = self.browser_handler.login(
                self.url,
                self.username,
                self.password,
                self.max_retries
            )

            if success:
                self.logger.info("登录成功,发送成功通知邮件...")
                notify_success(
                    f"登录成功URL:{page_titles['url']}\n"
                    f"登录页面标题: {page_titles['login']}\n"
                    f"登录后页面标题: {page_titles['after_login']}"
                )
            else:
                self.logger.error("登录失败，已达到最大重试次数")
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
            self.logger.error(error_msg)
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
    
    login_url = os.getenv('WEBSITE_URL')
    if not login_url.startswith(('http://', 'https://')):
            raise ValueError("WEBSITE_URL 必须以 http:// 或 https:// 开头")
    
    # 检查配置项的值合法性
    schedule_type = os.getenv('LOGIN_SCHEDULE_TYPE')
    if schedule_type not in ['monthly', 'minutes']:
        raise ValueError("LOGIN_SCHEDULE_TYPE 必须是 'monthly' 或 'minutes'")
    
    schedule_date = os.getenv('LOGIN_SCHEDULE_DATE')
    if not schedule_date.isdigit() or not (1 <= int(schedule_date) <= 31):
        raise ValueError("LOGIN_SCHEDULE_DATE 必须是1到31之间的数字")
    
    schedule_time = os.getenv('LOGIN_SCHEDULE_TIME')
    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', schedule_time):
        raise ValueError("LOGIN_SCHEDULE_TIME 必须是有效的24小时制时间格式(HH:MM)")
    
    max_retries = os.getenv('MAX_RETRIES')
    if not max_retries.isdigit() or not (1 <= int(max_retries) <= 10):
        raise ValueError("MAX_RETRIES 必须是1到10之间的数字")

def signal_handler(signum, frame):
    """处理终止信号"""
    from logger_helper import LoggerHelper
    logger = LoggerHelper.get_task_logger("auto_login")
    
    signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logger.info(f"收到{signal_name}信号，任务即将终止。")

    # 由于我们使用killpg向整个进程组发送信号，操作系统会负责清理子进程(浏览器和驱动)。
    # 此处不再需要手动调用cleanup或shutdown，否则会与系统级的信号处理产生竞态条件。
    
    sys.exit(0)

def main():
    from logger_helper import LoggerHelper
    # 使用任务日志 - 只记录到任务日志文件，不输出到控制台或系统日志
    logger = LoggerHelper.get_task_logger("auto_login")
    
    # 检查是否已经有进程在运行
    try:
        import subprocess
        ps_output = subprocess.check_output(["ps", "-ef"], text=True)
        current_pid = os.getpid()
        count = 0
        
        # 查找包含auto_login.py的进程
        for line in ps_output.splitlines():
            if "auto_login.py" in line and "python" in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        if pid != current_pid:  # 不计算当前进程
                            count += 1
                    except ValueError:
                        pass
        
        # 如果已经有其他进程在运行，则退出
        if count > 0:
            logger.warning(f"检测到已有 {count} 个auto_login.py进程在运行，本进程将退出")
            sys.exit(0)
    except Exception as e:
        logger.warning(f"检查进程状态失败: {str(e)}")
    
    # 日志打印当前的时区和时间
    logger.info(f"任务开始执行，当前时区: {time.strftime('%Z')}，当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    global scheduler
    try:
        # 注册信号处理器
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        validate_env_vars()

        auto_login = AutoLogin()
        login_schedule_type = os.getenv('LOGIN_SCHEDULE_TYPE')
        login_schedule_date = os.getenv('LOGIN_SCHEDULE_DATE')
        login_schedule_time = os.getenv('LOGIN_SCHEDULE_TIME')
        hour, minute = login_schedule_time.split(':')

        # 创建后台调度器并启动
        scheduler = BackgroundScheduler()
        scheduler.start()     
        
        if login_schedule_type == 'monthly':
            logger.info(f"每月 {login_schedule_date} 号 {login_schedule_time} 时自动进行登录...")
            # 使用cron触发器设置每月执行
            trigger = CronTrigger(
                day=login_schedule_date,
                hour=hour,
                minute=minute
            )
            job = scheduler.add_job(
                auto_login.attempt_login,
                trigger=trigger,
                name='monthly_login'
            )
            logger.info("调度程序已启动，按Ctrl+C可以停止...")
            logger.info(f"下次调度时间: {job.next_run_time}")
            
            # 立即执行一次登录任务
            logger.info("立即执行一次登录任务...")
            auto_login.attempt_login()
                
        elif login_schedule_type == 'minutes':
            logger.info("测试 - 使用分钟级调度, 每3分钟登录一次...")
            # 使用interval触发器设置每分钟执行
            trigger = IntervalTrigger(minutes=3)
            job = scheduler.add_job(
                auto_login.attempt_login,
                trigger=trigger,
                name='minute_login'
            )           
            logger.info("调度程序已启动，按Ctrl+C可以停止...")
            logger.info(f"下次调度时间: {job.next_run_time}")
            
            # 立即执行一次登录任务
            logger.info("立即执行一次登录任务...")
            auto_login.attempt_login()
        
        # 主循环使用较长的休眠时间-秒
        while True:
            time.sleep(3600)

    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        notify_failure(f"自动登录调度任务异常: {e}")
        # 发生异常时也要确保调度器停止
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)

if __name__ == "__main__":
    main()