# 标准 Shell 命令测试

## 任务描述
Shell 任务脚本示例，演示Shell脚本的标准开发模式。

## 执行文件
- `example_task_script.sh` - 示例Shell脚本

## 配置说明
- **调度**: 每3分钟执行一次 (`*/3 * * * *`)
- **超时**: 5秒
- **重试**: 2次，间隔60秒
- **状态**: 默认启用

## 执行模式
支持以下执行模式：
- `success` - 成功执行（默认）
- `business_failure` - 业务失败
- `technical_failure` - 技术失败

## 环境变量
- `API_KEY` - API密钥
- `REGION` - 区域设置
- `TASK_ID` - 任务ID（自动设置）

## 权限要求
确保脚本有执行权限：
```bash
chmod +x example_task_script.sh
```

## 日志输出
日志文件：`logs/task_shell_task_test.log`