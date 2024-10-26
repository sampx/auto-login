#!/bin/bash

# 设置错误时立即退出
set -e

# 定义镜像和容器名称
IMAGE_NAME="auto-login"
CONTAINER_NAME="auto-login-test"
TAG="latest"

echo "🚀 开始运行测试容器..."

# 检查是否存在同名容器，如果存在则删除
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "发现已存在的测试容器，正在删除..."
    docker rm -f ${CONTAINER_NAME}
fi

# 运行测试容器
echo "启动测试容器..."
docker run --name ${CONTAINER_NAME} \
    --env-file .env \
    -v $(pwd)/.env.test:/app/.env \
    ${IMAGE_NAME}:${TAG} \
    python test_login.py

# 检查测试结果
if [ $? -eq 0 ]; then
    echo "✅ 测试完成！"
else
    echo "❌ 测试失败！"
    exit 1
fi

# 清理容器
echo "清理测试容器..."
docker rm -f ${CONTAINER_NAME}
