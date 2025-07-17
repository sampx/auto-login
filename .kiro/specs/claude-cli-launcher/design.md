# 设计文档

## 概述

设计一个名为 `mycld` 的 shell 脚本，作为 claude cli 的启动器。该脚本将根据不同的命令行参数加载相应的环境配置文件，验证必要的环境变量，然后启动 claude cli。脚本支持两种主要模式：直接模式（无参数）和配置模式（带参数）。

## 项目结构

脚本将放置在项目的 `tools` 目录下：

```
项目根目录/
├── tools/
│   └── mycld           # Claude CLI 启动脚本
├── 其他项目文件...
```

需要先创建 `tools` 目录来存放该脚本。脚本创建后需要设置执行权限：`chmod +x tools/mycld`

## 架构

### 整体架构

```
用户输入 → 参数解析 → 环境验证 → 配置加载 → Claude CLI 启动
```

### 核心组件

1. **参数解析器** - 解析命令行参数并确定运行模式
2. **环境验证器** - 检查依赖和环境变量
3. **配置加载器** - 根据参数加载相应的配置文件
4. **CLI 启动器** - 启动 claude 命令并传递参数

## 组件和接口

### 1. 参数解析器 (parse_arguments)

**职责：** 解析命令行参数并确定脚本运行模式

**输入：** 命令行参数数组 `$@`

**输出：** 设置全局变量
- `MODE`: 运行模式 (direct/k2/anyrouter)
- `VERBOSE`: 是否启用详细输出
- `CLAUDE_ARGS`: 传递给 claude 的参数

**接口：**
```bash
parse_arguments() {
    # 解析 --help, -h, --verbose, -v, --k2, --anyrouter
    # 设置相应的全局变量
    # 处理无效参数的错误情况
}
```

### 2. 环境验证器 (validate_environment)

**职责：** 验证 claude cli 安装和必要的环境变量

**输入：** 当前运行模式

**输出：** 验证结果（成功/失败）

**接口：**
```bash
validate_environment() {
    local mode=$1
    # 检查 claude 命令是否存在
    # 根据模式验证环境变量
    # 返回验证结果
}
```

### 3. 配置加载器 (load_configuration)

**职责：** 根据运行模式加载相应的配置文件

**输入：** 运行模式

**输出：** 加载配置文件并设置环境变量

**接口：**
```bash
load_configuration() {
    local mode=$1
    # 根据模式 source 相应的 .zrc 文件
    # 处理文件不存在的情况
}
```

### 4. CLI 启动器 (launch_claude)

**职责：** 启动 claude cli 并传递参数

**输入：** claude 参数数组

**输出：** 启动 claude 进程

**接口：**
```bash
launch_claude() {
    # 使用 exec 启动 claude 命令
    # 传递所有参数
}
```

## 数据模型

### 运行模式枚举
```bash
# 运行模式
MODE_DIRECT="direct"      # 直接模式，不加载配置
MODE_K2="k2"             # K2 配置模式
MODE_ANYROUTER="anyrouter" # AnyRouter 配置模式
```

### 配置文件路径
```bash
# 配置文件路径
CONFIG_DIR="$HOME/tools/mac_zsh"
K2_CONFIG="$CONFIG_DIR/k2.zrc"
ANYROUTER_CONFIG="$CONFIG_DIR/anyrouter.zrc"
```

### 环境变量验证规则
```bash
# 必需的环境变量（仅在配置模式下）
REQUIRED_VARS=("ANTHROPIC_BASE_URL" "ANTHROPIC_AUTH_TOKEN")
```

## 错误处理

### 错误类型和处理策略

1. **命令行参数错误**
   - 无效参数：显示错误信息和帮助文本，退出码 1
   - 冲突参数：显示错误信息，退出码 1

2. **依赖检查错误**
   - claude cli 未安装：显示安装提示，退出码 2
   - 配置文件不存在：显示文件路径和创建提示，退出码 3

3. **环境变量错误**
   - 必需变量缺失：显示缺失的变量名，退出码 4
   - 直接模式下存在配置变量：显示警告信息，退出码 5

4. **配置加载错误**
   - 配置文件语法错误：显示文件路径和错误信息，退出码 6

### 错误信息格式
```bash
# 错误信息格式
error_message() {
    echo "❌ 错误: $1" >&2
    echo "💡 建议: $2" >&2
}
```

## 测试策略

### 单元测试场景

1. **参数解析测试**
   - 测试所有有效参数组合
   - 测试无效参数处理
   - 测试帮助信息显示

2. **环境验证测试**
   - 测试 claude cli 存在/不存在情况
   - 测试环境变量存在/缺失情况
   - 测试不同模式下的验证逻辑

3. **配置加载测试**
   - 测试配置文件存在/不存在情况
   - 测试配置文件加载后的环境变量设置
   - 测试配置文件语法错误处理

4. **集成测试**
   - 测试完整的启动流程
   - 测试参数传递给 claude cli
   - 测试详细输出模式

### 测试数据准备
```bash
# 创建测试用的配置文件
setup_test_configs() {
    mkdir -p "$TEST_CONFIG_DIR"
    echo 'export ANTHROPIC_BASE_URL="https://api.k2.com"' > "$TEST_CONFIG_DIR/k2.zrc"
    echo 'export ANTHROPIC_AUTH_TOKEN="test-token-k2"' >> "$TEST_CONFIG_DIR/k2.zrc"
}
```

## 实现细节

### 脚本结构
```bash
#!/bin/bash

# 全局变量定义
# 工具函数定义
# 核心功能函数定义
# 主函数
# 脚本入口点
```

### 详细输出实现
```bash
verbose_log() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo "🔍 [DEBUG] $1" >&2
    fi
}

info_log() {
    echo "ℹ️  $1" >&2
}
```

### 帮助信息设计
```bash
show_help() {
    cat << EOF
mycld - Claude CLI 启动器

用法:
    mycld [选项] [claude参数...]

选项:
    --k2            使用 K2 配置启动
    --anyrouter     使用 AnyRouter 配置启动
    -v, --verbose   显示详细输出
    -h, --help      显示此帮助信息

示例:
    mycld                           # 直接启动 claude
    mycld --k2 chat                 # 使用 K2 配置启动 claude chat
    mycld --anyrouter --verbose     # 使用 AnyRouter 配置并显示详细信息
EOF
}
```

### 安全考虑

1. **路径安全**
   - 使用绝对路径引用配置文件
   - 验证配置文件存在性和可读性

2. **环境变量安全**
   - 不在日志中显示敏感的环境变量值
   - 验证环境变量格式的合法性

3. **参数传递安全**
   - 正确处理包含空格的参数
   - 防止命令注入攻击

### 性能优化

1. **快速启动**
   - 最小化环境检查时间
   - 延迟加载非必需的配置

2. **内存使用**
   - 避免不必要的变量存储
   - 及时清理临时变量