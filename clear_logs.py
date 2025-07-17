#!/usr/bin/env python3
"""
清理日志目录中所有.log文件的脚本。
此脚本会清空文件内容，但不会删除文件本身。
"""
import os
import glob

def clear_all_logs():
    """
    查找 logs/ 目录下的所有 .log 文件并清空其内容。
    """
    logs_dir = "logs"
    
    # 确保日志目录存在
    if not os.path.exists(logs_dir):
        print(f"日志目录 '{logs_dir}' 不存在，无需清理。")
        return

    # 查找所有.log文件
    log_files = glob.glob(os.path.join(logs_dir, '*.log'))
    
    if not log_files:
        print(f"在 '{logs_dir}' 目录中未找到.log日志文件。")
        return

    print("开始清理日志文件...")
    for log_file in log_files:
        try:
            # 以写模式打开文件会清空其内容
            with open(log_file, 'w') as f:
                pass  # 不需要写入任何内容
            print(f"  - 已清空: {log_file}")
        except Exception as e:
            print(f"  - 清空失败: {log_file} (错误: {e})")
    
    print("日志清理完成。")

if __name__ == "__main__":
    clear_all_logs()
