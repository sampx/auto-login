#!/bin/bash

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 在启动前清理日志
echo "正在清理旧日志..."
python3 clear_logs.py
echo "" # 添加一个空行以提高可读性

# 只启动Web界面，不自动启动登录任务
# 用户可以通过Web界面手动启动任务
echo "启动Web任务管理器界面..."
python3 web_interface.py