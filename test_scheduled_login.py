import time
from auto_login import main
import threading

def run_main():
    main()

if __name__ == "__main__":
    print("开始测试定时登录功能...")
    
    # 在后台线程中运行main函数
    main_thread = threading.Thread(target=run_main)
    main_thread.start()
    
    # 让程序运行5分钟
    time.sleep(300)
    
    print("测试完成,程序将退出")
