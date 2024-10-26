from email_notifier import EmailNotifier

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