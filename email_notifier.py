import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from logger_helper import setup_logging

class EmailNotifier:
    def __init__(self):
        setup_logging() # Ensure logging is set up
        self.logger = logging.getLogger(__name__)        
        # 初始化发件人邮箱、密码、收件人邮箱、SMTP服务器和端口
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.recipient_email = os.getenv('EMAIL_RECIPIENT')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = os.getenv('SMTP_PORT')
        self.logger.debug(f"EMAIL_SENDER: {self.sender_email}")
        self.logger.debug(f"EMAIL_PASSWORD: {self.sender_password}")
        self.logger.debug(f"EMAIL_RECIPIENT: {self.recipient_email}")
        self.logger.debug(f"SMTP_SERVER: {self.smtp_server}")
        self.logger.debug(f"SMTP_PORT: {self.smtp_port}")

    def send_notification(self, subject, message):
        # 添加调试信息
        self.logger.info(f"发送邮件通知，主题: {subject}, 内容: {message}")
        # 打印smtp参数
        self.logger.debug(f"SMTP服务器: {self.smtp_server}, 端口: {self.smtp_port}")
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = subject
        # 添加邮件正文
        msg.attach(MIMEText(message, 'plain', 'utf-8'))

        try:
            # 使用SMTP_SSL连接到SMTP服务器并发送邮件
            try:
                smtp_port_int = int(self.smtp_port)
                server = smtplib.SMTP_SSL(self.smtp_server, smtp_port_int)
            except ValueError:
                self.logger.error(f"SMTP 端口 '{self.smtp_port}' 无效，必须是整数。")
                return
            except Exception as e:
                self.logger.error(f"无法连接到 SMTP 服务器 {self.smtp_server}:{self.smtp_port}: {str(e)}")
                return

            with server:
                self.logger.debug("SSL连接已建立")
                server.login(self.sender_email, self.sender_password)
                self.logger.debug("登录成功")
                server.send_message(msg)
                self.logger.info("通知邮件发送完成。")
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP 认证错误: {str(e)}")
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"SMTP 连接错误: {str(e)}")
        except smtplib.SMTPHeloError as e:
            self.logger.error(f"SMTP HELO 错误: {str(e)}")
        except smtplib.SMTPDataError as e:
            self.logger.error(f"SMTP 数据错误: {str(e)}")
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP 通用错误: {str(e)}")
        except Exception as e:            
            self.logger.error(f"未知错误: {str(e)}")

def notify_success(additional_info=""):
    setup_logging() # Ensure logging is set up
    logger = logging.getLogger(notify_success.__name__)  
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
    setup_logging() # Ensure logging is set up
    logger = logging.getLogger(notify_failure.__name__)  
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

