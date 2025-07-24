#!/bin/bash

# 激活虚拟环境（如果使用）
source venv/bin/activate

# 在启动前清理日志
# echo "正在清理旧日志..."
# python3 clear_logs.py
# echo "" # 添加一个空行以提高可读性

# 检查命令行参数
LOG_LEVEL_ARG=""
if [ "$1" == "--debug" ]; then
    LOG_LEVEL_ARG="export LOG_LEVEL=DEBUG"
    echo "以 DEBUG 模式启动..."
fi

# 检查端口是否被占用并清理
WEB_PORT=${WEB_PORT:-5001}
echo "检查端口 ${WEB_PORT} 占用情况..."
lsof -ti:${WEB_PORT} | xargs kill -9 2>/dev/null || true
sleep 2

# 启动统一的Web应用
echo "启动统一Web应用 (端口: ${WEB_PORT})..."
${LOG_LEVEL_ARG}
export WEB_PORT=${WEB_PORT}
python3 app.py

echo "Web应用已关闭"