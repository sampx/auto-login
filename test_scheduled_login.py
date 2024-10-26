import time
from auto_login import main
import threading
import os
from dotenv import load_dotenv

def run_main():
    main()

if __name__ == "__main__":
    print("开始测试定时登录功能...")
    
    # 在后台线程中运行main函数
    main_thread = threading.Thread(target=run_main)
    main_thread.daemon = True  # 设置为后台线程
    main_thread.start()
    print("主线程已启动，测试程序将继续运行...")
    
    # 设置程序运行的总时间（比如10分钟），以便观察调度任务
    test_duration = 3 * 60  
    start_time = time.time()

    try:
        while time.time() - start_time < test_duration:
            time.sleep(60)  # 每分钟输出一次
            print(f"程序已运行 {int((time.time() - start_time) / 60)} 分钟")
    except KeyboardInterrupt:
        print("程序被手动终止")

    print("测试已结束")
