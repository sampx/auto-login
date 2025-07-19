#!/bin/bash

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 在启动前清理日志
echo "正在清理旧日志..."
python3 clear_logs.py
echo "" # 添加一个空行以提高可读性

# 检查端口是否被占用并清理
echo "检查端口占用情况..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
sleep 2

# 启动新版任务调度器API（端口5002）
echo "启动新版任务调度器API（端口5002）..."
nohup python3 scheduler_api.py > logs/scheduler_api.log 2>&1 &
SCHEDULER_API_PID=$!
echo "新版任务调度器API已启动 (PID: $SCHEDULER_API_PID)"

# 等待API服务器启动
echo "等待API服务器启动..."
sleep 5

# 启动老版本Web界面（使用端口5001，如果被占用则尝试5003）
echo "启动老版本Web任务管理器界面..."
export WEB_PORT=5001
python3 web_interface.py || {
    echo "端口5001被占用，尝试使用端口5003..."
    export WEB_PORT=5003
    python3 web_interface.py
}

# 清理：当web_interface.py退出时，关闭所有服务
echo "正在关闭所有服务..."
kill $SCHEDULER_API_PID 2>/dev/null || true
echo "所有服务已关闭"