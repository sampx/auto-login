#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务调度引擎 - 示例任务脚本模版 (Python 版本)

本脚本旨在演示如何根据《任务脚本开发指南》编写一个标准的、
可被调度引擎管理的 Python 任务。

使用方法:
1. 在调度引擎的 Web UI 中编辑任务。
2. 将"任务执行"字段设置为: python tasks/{task_id}.py <mode>
   - <mode> 可以是 success, business_failure, 或 technical_failure
3. 确保脚本有执行权限: chmod +x tasks/{task_id}.py
4. 配置自定义环境变量,例如: API_KEY=your_secret_key, REGION=us-east-1
5. 保存并触发任务,观察其日志和最终状态。
"""

import os
import sys
import time
from datetime import datetime

# --- 函数定义 ---

def log_info(message):
    """打印普通日志 (到 stdout)"""
    print(f"[信息] {message}")

def log_error(message):
    """打印错误日志 (到 stderr)"""
    print(f"[错误] {message}", file=sys.stderr)

# --- 主逻辑开始 ---

def main():
    log_info("========================================")
    log_info("Python 任务脚本开始执行...")
    log_info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_info("========================================")

    # 1. 读取环境变量
    # 使用 os.environ.get 来为变量提供一个默认值
    task_id = os.environ.get("TASK_ID", "unknown")
    task_log = os.environ.get("TASK_LOG", "unknown")
    
    log_info(f"任务ID: {task_id}")
    log_info(f"任务日志: {task_log}")

    # 2. 模拟业务逻辑
    # 从第一个命令行参数获取模拟的执行结果
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        # 如果没有提供参数,使用 success
        mode = "success"

    log_info(f"当前模拟模式为: {mode}")

    # 模拟执行耗时
    time.sleep(2)

    # 3. 根据结果使用正确的退出码
    if mode == "success":
        log_info("所有操作均已成功完成。")
        log_info("任务执行结束。")
        sys.exit(0)  # 退出码 0: 执行成功
    elif mode == "business_failure":
        log_error("业务失败: 无法从目标源找到所需的业务数据。")
        log_error("这是一个可预期的失败,任务将不会重试。")
        log_info("任务执行结束。")
        sys.exit(1)  # 退出码 1: 业务失败
    elif mode == "technical_failure":
        log_error("技术失败: 连接到远程服务器时发生网络超时。")
        log_error("这是一个非预期的技术故障,引擎将根据配置进行重试。")
        log_info("任务执行结束。")
        sys.exit(2)  # 退出码 2: 技术失败
    else:
        log_error(f"未知的模式: '{mode}'。请使用 'success', 'business_failure', 或 'technical_failure'。")
        sys.exit(1)  # 将未知模式也视为业务失败

if __name__ == "__main__":
    main()