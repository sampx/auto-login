---
inclusion: always
---

# Project Structure

## Root Directory Layout

```
├── app.py                  # Unified Flask web server (port 5001)
├── api_blueprint.py        # Modern scheduler API blueprint
├── scheduler_engine.py     # Generic task scheduling engine
├── browser_handler.py      # Browser automation logic
├── email_notifier.py       # Email notification functionality
├── logger_helper.py        # Logging configuration and management
├── clear_logs.py           # Log cleanup utility
├── requirements.txt        # Python dependencies
├── start_web_app.sh        # Web interface startup script
├── .env.example            # Environment template
├── .env                    # Production config (not in git)
├── .gitignore              # Git ignore patterns
├── README.md               # Project documentation
├── LICENSE                 # License file
├── CLAUDE.md               # Claude AI documentation
├── docker/                 # Docker configuration directory
│   ├── Dockerfile          # Container configuration
│   ├── .dockerignore       # Docker build exclusions
│   ├── build.sh            # Docker image building script
│   ├── start_docker.sh     # Docker container startup script
│   └── docker_entrypoint.sh # Container entry point script
├── docs/                   # Project documentation
│   ├── REFACTOR_SUMMARY.md # JavaScript refactoring summary
│   ├── scheduler_enhancement_suggestions.md # Enhancement suggestions
│   ├── task_script_development_guide.md # Task development guide
│   └── tmp.txt             # Temporary documentation
├── logs/                   # Application logs
│   ├── sys.log             # System logs
│   ├── task_auto_login.log # Task execution logs
│   ├── task_claude_endpoint_check.log # Claude endpoint check logs
│   ├── task_python_task_test.log # Python task test logs
│   ├── task_shell_task_test.log # Shell task test logs
│   └── task_test_task.log  # Test task logs
├── web/                    # Web interface files
│   ├── static/             # Static resource files
│   │   ├── css/            # CSS style files
│   │   │   └── main.css    # Main stylesheet
│   │   └── js/             # Modular JavaScript architecture
│   │       ├── core/       # Core modules
│   │       │   ├── state.js    # Global state management
│   │       │   ├── api.js      # API requests and connection management
│   │       │   ├── utils.js    # Common utility functions
│   │       │   └── ui.js       # UI operations and messaging
│   │       ├── modules/    # Feature modules
│   │       │   ├── logs.js     # Log management functionality
│   │       │   └── scheduler.js # Task scheduler functionality
│   │       └── main.js     # Main entry point (80 lines)
│   └── templates/          # Flask HTML templates
│       └── index.html      # Unified task management UI
├── tasks/                  # Task scripts directory
│   ├── claude_endpoint_check/  # Claude endpoint check task directory
│   │   ├── config.json         # Task configuration
│   │   ├── claude_endpoint_check.py # Task script
│   │   └── README.md           # Task documentation
│   ├── python_task_test/       # Python task test directory
│   │   ├── config.json         # Task configuration
│   │   ├── example_task_script.py # Task script
│   │   └── README.md           # Task documentation
│   ├── shell_task_test/        # Shell task test directory
│   │   ├── config.json         # Task configuration
│   │   ├── example_task_script.sh # Task script
│   │   └── README.md           # Task documentation
│   ├── test_simple/            # Simple test task directory
│   │   ├── config.json         # Task configuration
│   │   └── test_task.py        # Task script
│   └── test_task/              # Test task directory
│       ├── config.json         # Task configuration
│       ├── test_task.py        # Task script
│       └── README.md           # Task documentation
├── tests/                  # Test files directory
│   ├── .env.test           # Test environment configuration
│   ├── config_extended.json # Extended test configuration
│   ├── test_docker.sh      # Docker test script
│   ├── test_email_notifier.py # Email notifier tests
│   ├── test_env_loading.py # Environment loading tests
│   ├── test_login.py       # Login functionality tests
│   ├── test_scheduler.py   # Scheduler tests
│   └── test_scheduler_api.py # Scheduler API tests
├── tools/                  # Utility tools
│   └── mycld               # CLI tool
└── .kiro/                  # Kiro configuration
    ├── specs/              # Feature specifications
    │   ├── claude-cli-launcher/ # Claude CLI launcher spec
    │   ├── duplicate-logging-fix/ # Duplicate logging fix spec
    │   ├── General-Scheduling-Engine/ # General scheduling engine spec
    │   └── web-task-manager/ # Web task manager spec
    └── steering/           # Development guidelines
        ├── product.md      # Product guidelines
        ├── structure.md    # Structure guidelines
        └── tech.md         # Technical guidelines
```

## Core Modules

### Unified Web Server (`app.py`)
- Main Flask application serving the unified task management UI
- Registers the modern scheduler API blueprint
- Serves static files and templates from `web/` directory
- Port 5001 for all web services
- Initializes and manages the scheduler engine

### API Blueprint (`api_blueprint.py`)
- Modern scheduler API blueprint for `/api/scheduler/tasks/*` endpoints
- Configuration and logging APIs (`/api/config`, `/api/scheduler/validate-cron`)
- Task management operations (CRUD, execute, toggle, logs)
- Transaction management and file locking for data integrity

### Frontend Architecture (Modular JavaScript)
#### Core Modules (`web/static/js/core/`)
- **`state.js`** - Global state management with StateManager (95 lines)
- **`api.js`** - API requests, connection management, and health checks (150 lines)
- **`utils.js`** - Common utility functions and helpers (85 lines)
- **`ui.js`** - UI operations, messaging, and modal management (200 lines)

#### Feature Modules (`web/static/js/modules/`)
- **`logs.js`** - Log management functionality (280 lines)
- **`scheduler.js`** - Task scheduler with CRUD operations (450 lines)

#### Main Entry (`web/static/js/main.js`)
- Coordinated initialization and global event handling (80 lines)
- Module loading and compatibility layer
- Event binding and cleanup management

### Scheduling Services
#### Generic Scheduler (`scheduler_engine.py`)
- Generic task scheduling engine with APScheduler
- Cron-based task management with file monitoring
- Task execution with subprocess management
- Configuration file watching (watchdog or polling)
- Transaction management for task operations

### Core Components
#### Browser Handler (`browser_handler.py`)
- Playwright browser management
- Login automation logic
- Page interaction and status checking
- Resource cleanup

#### Email Notifier (`email_notifier.py`)
- SMTP email functionality
- Success/failure notifications
- Configurable email templates

#### Logger Helper (`logger_helper.py`)
- Centralized logging configuration
- Log reading and filtering
- Log formatting and rotation management

## Configuration Files

### Environment Files
- `.env` - Production configuration (never commit)
- `.env.test` - Test environment settings
- `.env.example` - Template with all required variables

### Docker Files
- `Dockerfile` - Container build configuration
- `.dockerignore` - Files to exclude from build context

## Shell Scripts

- `docker/build.sh` - Docker image building
- `docker/start_docker.sh` - Docker container startup
- `start_web_app.sh` - Web interface startup

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