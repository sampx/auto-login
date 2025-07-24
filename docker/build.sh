#!/bin/bash

# 设置错误时立即退出
set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# 定义镜像名称和标签
IMAGE_NAME="auto-login"
TAG="latest"

# 输出开始构建信息
echo "开始构建 Docker 镜像: ${IMAGE_NAME}:${TAG}"
echo "项目根目录: $PROJECT_ROOT"

# 检查Dockerfile是否存在
DOCKERFILE_PATH="$SCRIPT_DIR/Dockerfile"
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "❌ 错误: Dockerfile 不存在于 $DOCKERFILE_PATH"
    exit 1
fi

# 构建Docker镜像
docker build -t ${IMAGE_NAME}:${TAG} -f "$DOCKERFILE_PATH" "$PROJECT_ROOT"

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功！"
    echo "镜像信息："
    docker images | grep ${IMAGE_NAME}
else
    echo "❌ Docker镜像构建失败！"
    exit 1
fi
