#!/bin/bash

# 设置错误时立即退出
set -e

# 定义镜像名称和标签
IMAGE_NAME="auto-login"
TAG="latest"

# 输出开始构建信息
echo "开始构建 Docker 镜像: ${IMAGE_NAME}:${TAG}"

# 构建Docker镜像
docker build -t ${IMAGE_NAME}:${TAG} .

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功！"
    echo "镜像信息："
    docker images | grep ${IMAGE_NAME}
else
    echo "❌ Docker镜像构建失败！"
    exit 1
fi
