#!/bin/bash

# docker_entrypoint.sh - Docker容器的入口点脚本
# 默认启动Web界面，不自动启动后台任务

# 设置错误时立即退出
set -e

echo "🚀 启动Web任务管理器..."

# 创建日志目录（如果不存在）
mkdir -p /app/logs

# 设置日志文件权限
touch /app/logs/app.log
chmod 666 /app/logs/app.log

# 启动Web界面
echo "✅ 启动Web界面服务..."
exec python web_interface.py