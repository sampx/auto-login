#!/bin/bash

# 设置错误时立即退出
set -e

# 定义镜像和容器名称
IMAGE_NAME="auto-login"
CONTAINER_NAME="auto-login"
TAG="latest"

echo "🚀 开始运行容器..."

# 检查是否存在同名容器，如果存在则删除
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "发现已存在的测试容器，正在删除..."
    docker rm -f ${CONTAINER_NAME}
fi

# 运行容器
echo "启动容器..."
docker run -d --name ${CONTAINER_NAME} \
    --env-file .env \
    -v $(pwd)/.env:/app/.env \
    ${IMAGE_NAME}:${TAG} 

echo "容器启动完成！"
