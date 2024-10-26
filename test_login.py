import os
from dotenv import load_dotenv
from auto_login import AutoLogin

# 从.env.test文件载环境变量
load_dotenv('.env.test',override=True)
def test_login():   
    print("开始登录测试...")
    auto_login = AutoLogin()
    auto_login.attempt_login()

if __name__ == "__main__":
    test_login()
