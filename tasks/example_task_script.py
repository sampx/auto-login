#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务调度引擎 - 示例任务脚本

本脚本旨在演示如何根据《任务脚本开发指南》编写一个标准的、可被调度引擎管理的任务。
它包含了日志输出、环境变量读取和退出码使用的最佳实践。

使用方法:
1. 在调度引擎的 Web UI 中创建一个新任务。
2. 将“任务执行”字段设置为: python tasks/example_task_script.py <mode>
   - <mode> 可以是 success, business_failure, 或 technical_failure
3. 配置自定义环境变量,例如: API_KEY=your_secret_key, REGION=us-east-1
4. 保存并触发任务,观察其日志和最终状态。
"""

import os
import sys
import time
import random

def main():
    """主执行函数"""

    print("========================================")
    print(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("========================================")

    # 1. 读取环境变量
    # -------------------
    task_id = os.environ.get('TASK_ID', 'unknown')
    api_key = os.environ.get('API_KEY', '未提供')
    region = os.environ.get('REGION', '默认区域')

    print(f"\n[信息] 任务ID: {task_id}")
    print(f"[信息] 自定义环境变量 API_KEY: {api_key}")
    print(f"[信息] 自定义环境变量 REGION: {region}\n")

    # 2. 模拟业务逻辑
    # -------------------
    # 从命令行参数获取模拟的执行结果
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        # 如果没有提供参数,则随机选择一种模式
        mode = random.choice(["success", "business_failure", "technical_failure"])

    print(f"[信息] 当前模拟模式为: {mode}\n")

    time.sleep(2) # 模拟执行耗时

    # 3. 根据结果使用正确的退出码
    # ---------------------------------
    if mode == "success":
        print("[成功] 所有操作均已成功完成。")
        print("任务执行结束。")
        sys.exit(0) # 退出码 0: 执行成功

    elif mode == "business_failure":
        # 使用 sys.stderr 输出错误信息
        sys.stderr.write("[业务失败] 无法从目标源找到所需的业务数据。\n")
        sys.stderr.write("这是一个可预期的失败,任务将不会重试。\n")
        print("任务执行结束。")
        sys.exit(1) # 退出码 1: 业务失败

    elif mode == "technical_failure":
        sys.stderr.write("[技术失败] 连接到远程服务器时发生网络超时。\n")
        sys.stderr.write("这是一个非预期的技术故障,引擎将根据配置进行重试。\n")
        print("任务执行结束。")
        sys.exit(2) # 退出码 2: 技术失败

    else:
        sys.stderr.write(f"[错误] 未知的模式: {mode}。请使用 'success', 'business_failure', 或 'technical_failure'。\n")
        sys.exit(2) # 将未知模式也视为技术失败

if __name__ == "__main__":
    main()
