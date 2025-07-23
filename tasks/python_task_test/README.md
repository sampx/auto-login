# 标准 Python 任务

## 任务描述
Python任务脚本示例，演示标准的任务开发模式。

## 执行文件
- `example_task_script.py` - 示例Python脚本

## 配置说明
- **调度**: 每10分钟执行一次 (`*/10 * * * *`)
- **超时**: 3秒
- **重试**: 2次，间隔5秒
- **状态**: 默认禁用

## 执行模式
支持以下执行模式：
- `success` - 成功执行
- `business_failure` - 业务失败
- `technical_failure` - 技术失败（默认）

## 环境变量
- `API_KEY` - API密钥
- `REGION` - 区域设置

## 日志输出
日志文件：`logs/task_python_task_test.log`