# Claude API 端点检测

## 任务描述
检测 anyrouter api 可用性，确保Claude API服务正常运行。

## 执行文件
- `claude_endpoint_check.py` - API检测脚本

## 配置说明
- **调度**: 每3小时执行一次 (`0 */3 * * *`)
- **超时**: 30秒
- **重试**: 1次，间隔5秒
- **状态**: 默认启用

## 环境变量
需要以下环境变量：
- `ANTHROPIC_BASE_URL` - Claude API基础URL
- `ANTHROPIC_AUTH_TOKEN` - Claude API认证令牌
- `_ENV_FILE` - 额外的环境文件路径

## 返回码说明
- `0` - 检测成功
- `1` - 业务失败（API返回错误）
- `2` - 技术失败（网络错误等）

## 日志输出
日志文件：`logs/task_claude_endpoint_check.log`