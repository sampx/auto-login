import os
from dotenv import load_dotenv
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from email_notifier import EmailNotifier

# 从.env.test文件载环境变量
load_dotenv('.env.test',override=True)
def main():
    # 创建EmailNotifier实例
    notifier = EmailNotifier()

    # 定义测试邮件的主题和内容
    subject = "测试邮件主题"
    message = "这是一封测试邮件。"

    # 调用send_notification方法发送邮件
    notifier.send_notification(subject, message)

if __name__ == '__main__':
    main()