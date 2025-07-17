# Project Structure

## Root Directory Layout

```
├── auto_login.py           # Main application entry point
├── browser_handler.py      # Browser automation logic
├── email_notifier.py       # Email notification functionality
├── logger_helper.py        # Logging configuration and management
├── process_manager.py      # Process management functionality
├── task_manager.py         # Task management functionality
├── web_interface.py        # Flask web interface
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── .env.example            # Environment template
├── .env                    # Production config (not in git)
├── .env.test               # Test configuration
├── logs/                   # Application logs
├── static/                 # Static resource files
│   ├── css/                # CSS style files
│   └── js/                 # JavaScript files
├── templates/              # Flask HTML templates
└── .kiro/                  # Kiro configuration
```

## Core Modules

### Main Application (`auto_login.py`)
- Entry point and orchestration
- Scheduler configuration and management
- Signal handling for graceful shutdown
- Environment validation

### Browser Handler (`browser_handler.py`)
- Playwright browser management
- Login automation logic
- Page interaction and status checking
- Resource cleanup

### Email Notifier (`email_notifier.py`)
- SMTP email functionality
- Success/failure notifications
- Configurable email templates

### Process Manager (`process_manager.py`)
- 进程创建和监控
- 进程状态管理
- 资源使用统计
- 进程终止和清理

### Task Manager (`task_manager.py`)
- 任务模型和状态管理
- 任务操作（启动/停止）
- 任务调度
- 任务元数据管理

### Web Interface (`web_interface.py`)
- Flask Web服务器
- RESTful API接口
- 任务管理API
- 配置管理API
- 日志查看API

### Logger Helper (`logger_helper.py`)
- 日志配置
- 日志读取和过滤
- 日志格式化

## Configuration Files

### Environment Files
- `.env` - Production configuration (never commit)
- `.env.test` - Test environment settings
- `.env.example` - Template with all required variables

### Docker Files
- `Dockerfile` - Container build configuration
- `.dockerignore` - Files to exclude from build context

## Shell Scripts

- `build.sh` - Docker image building
- `start.sh` - Production container startup
- `test.sh` - Test execution
- `start_web_app.sh` - Combined app and web interface startup

## Naming Conventions

- **Files**: Snake case (e.g., `auto_login.py`)
- **Classes**: PascalCase (e.g., `BrowserHandler`)
- **Functions**: Snake case (e.g., `attempt_login`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)
- **Environment Variables**: UPPER_SNAKE_CASE

## Code Organization Patterns

- Each module has a single responsibility
- Environment variables centralized in `.env`
- Logging configured through `logger_helper.py`
- Error handling with try/catch and proper cleanup
- Signal handlers for graceful shutdown