#!/bin/bash

# 设置错误时立即退出
set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# 定义镜像和容器名称
IMAGE_NAME="auto-login"
CONTAINER_NAME="auto-login"
TAG="latest"

# .env 文件路径
ENV_FILE="$PROJECT_ROOT/.env"

echo "🚀 开始运行容器..."
echo "项目根目录: $PROJECT_ROOT"

# 检查 .env 文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 错误: .env 文件不存在于 $ENV_FILE"
    echo "请确保在项目根目录下存在 .env 文件"
    exit 1
fi

# 检查是否存在同名容器，如果存在则删除
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "发现已存在的测试容器，正在删除..."
    docker rm -f ${CONTAINER_NAME}
fi

# 运行容器
echo "启动容器..."
docker run -d --name ${CONTAINER_NAME} \
    --env-file "$ENV_FILE" \
    -v "$PROJECT_ROOT/.env:/app/.env" \
    -v "$PROJECT_ROOT/logs:/app/logs" \
    -v "$PROJECT_ROOT/tasks:/app/tasks" \
    -v "$PROJECT_ROOT/tools:/app/tools" \
    -v "$PROJECT_ROOT/env:/app/env" \
    -e TASK_CONFIG_MONITOR_TYPE=polling \
    -e TASK_CONFIG_POLLING_INTERVAL=10 \
    -p 5001:5001 \
    ${IMAGE_NAME}:${TAG}

echo "容器启动完成！"
