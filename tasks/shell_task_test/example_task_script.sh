#!/bin/bash

#
# 任务调度引擎 - 示例任务脚本 (Shell 版本)
#
# 本脚本旨在演示如何根据《任务脚本开发指南》编写一个标准的、
# 可被调度引擎管理的 Shell 任务。
#
# 使用方法:
# 1. 在调度引擎的 Web UI 中创建一个新任务。
# 2. 将“任务执行”字段设置为: /bin/bash tasks/example_task_script.sh <mode>
#    - <mode> 可以是 success, business_failure, 或 technical_failure
# 3. 确保脚本有执行权限: chmod +x tasks/example_task_script.sh
# 4. 配置自定义环境变量,例如: API_KEY=your_secret_key, REGION=us-east-1
# 5. 保存并触发任务,观察其日志和最终状态。
#

# --- 函数定义 ---

# 打印普通日志 (到 stdout)
log_info() {
  echo "[信息] $1"
}

# 打印错误日志 (到 stderr)
log_error() {
  echo "[错误] $1" >&2
}

# --- 主逻辑开始 ---

log_info "========================================"
log_info "Shell 任务脚本开始执行..."
log_info "执行时间: $(date)"
log_info "========================================"

# 1. 读取环境变量
# 使用 :- "default" 来为变量提供一个默认值
log_info "任务ID: ${TASK_ID:-"unknown"}"

# 2. 模拟业务逻辑
# 从第一个命令行参数 ($1) 获取模拟的执行结果
if [ -n "$1" ]; then
  MODE=$1
else
  # 如果没有提供参数,使用 success  
  MODE="success"  
fi

log_info "当前模拟模式为: $MODE"

# 模拟执行耗时
sleep 2

# 3. 根据结果使用正确的退出码
case "$MODE" in
  success)
    log_info "所有操作均已成功完成。"
    log_info "任务执行结束。"
    exit 0 # 退出码 0: 执行成功
    ;;
  business_failure)
    log_error "业务失败: 无法从目标源找到所需的业务数据。"
    log_error "这是一个可预期的失败,任务将不会重试。"
    log_info "任务执行结束。"
    exit 1 # 退出码 1: 业务失败
    ;;
  technical_failure)
    log_error "技术失败: 连接到远程服务器时发生网络超时。"
    log_error "这是一个非预期的技术故障,引擎将根据配置进行重试。"
    log_info "任务执行结束。"
    exit 2 # 退出码 2: 技术失败
    ;;
  *)
    log_error "未知的模式: '$MODE'。请使用 'success', 'business_failure', 或 'technical_failure'。"
    exit 1 # 将未知模式也视为业务失败
    ;;
esac
