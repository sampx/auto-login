import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)
# 配置日志输出
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# 加载环境变量
load_dotenv()

class EmailNotifier:
    def __init__(self):
        # 初始化发件人邮箱、密码、收件人邮箱、SMTP服务器和端口
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.recipient_email = os.getenv('EMAIL_RECIPIENT')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        logger.debug(f"EMAIL_SENDER: {self.sender_email}")
        logger.debug(f"EMAIL_PASSWORD: {self.sender_password}")
        logger.debug(f"EMAIL_RECIPIENT: {self.recipient_email}")
        logger.debug(f"SMTP_SERVER: {self.smtp_server}")
        logger.debug(f"SMTP_PORT: {self.smtp_port}")

    def send_notification(self, subject, message):
        # 添加调试信息
        logger.debug(f"发送邮件通知，主题: {subject}, 内容: {message}")
        # 打印smtp参数
        logger.debug(f"SMTP服务器: {self.smtp_server}, 端口: {self.smtp_port}")
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = subject
        # 添加邮件正文
        msg.attach(MIMEText(message, 'plain', 'utf-8'))

        try:
            # 使用SMTP_SSL连接到SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                logger.debug("SSL连接已建立")
                server.login(self.sender_email, self.sender_password)
                logger.debug("登录成功")
                server.send_message(msg)
                logger.info("邮件通知发送成功")
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP 认证错误: {str(e)}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP 连接错误: {str(e)}")
        except smtplib.SMTPHeloError as e:
            logger.error(f"SMTP HELO 错误: {str(e)}")
        except smtplib.SMTPDataError as e:
            logger.error(f"SMTP 数据错误: {str(e)}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 通用错误: {str(e)}")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")

def notify_success(additional_info=""):
    # 创建EmailNotifier实例
    notifier = EmailNotifier()
    message = "网站自动登录尝试成功。"
    if additional_info:
        message += f"\n\n{additional_info}"
    
    # 添加debug日志
    logger.debug(f"准备发送邮件通知，内容如下:\n{message}")
    
    # 发送成功通知邮件
    notifier.send_notification(
        "网站自动登录成功",
        message
    )

def notify_failure(error_message):
    # 创建EmailNotifier实例
    notifier = EmailNotifier()
    message = f"自动登录尝试失败。错误: {error_message}"
        
    # 添加debug日志
    logger.debug(f"准备发送邮件通知，内容如下:\n{message}")

    # 发送失败通知邮件
    notifier.send_notification(
        "网站自动登录失败",
        message
    )
