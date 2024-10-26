from auto_login import AutoLogin

def test_login():
    print("开始登录测试...")
    auto_login = AutoLogin()
    auto_login.attempt_login()

if __name__ == "__main__":
    test_login()
