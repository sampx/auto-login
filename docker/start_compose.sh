#!/bin/bash

# 设置错误时立即退出
set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# 定义 compose 文件路径
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# 定义服务名称
SERVICE_NAME="auto-login"

echo "🚀 开始启动 Docker Compose 服务..."
echo "项目根目录: $PROJECT_ROOT"
echo "Compose 文件: $COMPOSE_FILE"

# 检查 .env 文件是否存在
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 错误: .env 文件不存在于 $ENV_FILE"
    echo "请确保在项目根目录下存在 .env 文件"
    exit 1
fi

# 检查 Docker 是否正在运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ 错误: Docker 守护进程未运行"
    echo "请确保 Docker 正在运行"
    exit 1
fi

# 检查 docker-compose 或 docker compose 是否可用
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ 错误: 未找到 docker-compose 或 docker compose 命令"
    echo "请安装 Docker Compose"
    exit 1
fi

echo "使用命令: $COMPOSE_CMD"

# 检查是否存在正在运行的容器
EXISTING_CONTAINERS=$(docker ps -a --filter "name=${SERVICE_NAME}" --format "{{.Names}}")
if [ ! -z "$EXISTING_CONTAINERS" ]; then
    echo "发现已存在的容器: $EXISTING_CONTAINERS"
    
    # 检查是否有容器正在运行
    RUNNING_CONTAINERS=$(docker ps --filter "name=${SERVICE_NAME}" --format "{{.Names}}")
    if [ ! -z "$RUNNING_CONTAINERS" ]; then
        echo "正在运行的容器: $RUNNING_CONTAINERS"
        echo "正在停止正在运行的容器..."
        cd "$SCRIPT_DIR" && $COMPOSE_CMD down
        echo "✅ 已停止正在运行的容器"
    else
        echo "发现已停止的容器，正在清理..."
        cd "$SCRIPT_DIR" && $COMPOSE_CMD down
        echo "✅ 已清理已停止的容器"
    fi
else
    echo "未发现已存在的容器，准备启动新服务..."
fi

# 启动服务
echo "正在启动 Docker Compose 服务..."
cd "$SCRIPT_DIR" && $COMPOSE_CMD -f docker-compose.yml up -d --build

# 验证服务是否成功启动
echo "正在验证服务状态..."
sleep 2

if docker ps --filter "name=${SERVICE_NAME}" --filter "status=running" | grep -q "${SERVICE_NAME}"; then
    echo "✅ 容器启动成功！"
    
    # 显示端口映射信息
    PORT_MAPPINGS=$(docker port ${SERVICE_NAME} 2>/dev/null || echo "")
    if [ ! -z "$PORT_MAPPINGS" ]; then
        echo "端口映射信息:"
        docker port ${SERVICE_NAME}
    fi
    
    # 显示容器状态
    echo "容器状态:"
    docker ps --filter "name=${SERVICE_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "服务已启动，可以通过以下方式访问:"
    echo "- 查看日志: cd docker && $COMPOSE_CMD logs -f"
    echo "- 停止服务: cd docker && $COMPOSE_CMD down"
    echo "- 重启服务: cd docker && $COMPOSE_CMD restart"
else
    echo "❌ 容器启动失败"
    echo "查看错误日志:"
    cd "$SCRIPT_DIR" && $COMPOSE_CMD logs --tail=50
    exit 1
fi