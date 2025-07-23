---
inclusion: always
---

# Project Structure

## Root Directory Layout

```
├── app.py                  # Unified Flask web server (port 5001)
├── api_blueprint.py        # NEW VERSION: Scheduler API blueprint
├── legacy_api_blueprint.py # OLD VERSION: Legacy task API (DO NOT MODIFY)
├── auto_login.py           # Main scheduled login service
├── scheduler_engine.py     # NEW VERSION: Generic task scheduling engine
├── task_manager.py         # OLD VERSION: Legacy task management (DO NOT MODIFY)
├── browser_handler.py      # Browser automation logic
├── email_notifier.py       # Email notification functionality
├── logger_helper.py        # Logging configuration and management
├── process_manager.py      # Process management functionality
├── clear_logs.py           # Log cleanup utility
├── requirements.txt        # Python dependencies
├── start_docker.sh         # Docker container startup script
├── start_web_app.sh        # Web interface startup
├── .env.example            # Environment template
├── .env                    # Production config (not in git)
├── .gitignore              # Git ignore patterns
├── README.md               # Project documentation
├── LICENSE                 # License file
├── CLAUDE.md               # Claude AI documentation
├── GEMINI.md               # Gemini AI documentation
├── .docker/                # Docker configuration directory
│   ├── Dockerfile          # Container configuration
│   ├── .dockerignore       # Docker build exclusions
│   ├── build.sh            # Docker image building script
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
├── static/                 # Static resource files
│   ├── css/                # CSS style files
│   │   └── style.css       # Main stylesheet
│   └── js/                 # Modular JavaScript architecture
│       ├── core/           # Core modules
│       │   ├── state.js    # Global state management
│       │   ├── api.js      # API requests and connection management
│       │   ├── utils.js    # Common utility functions
│       │   └── ui.js       # UI operations and messaging
│       ├── modules/        # Feature modules
│       │   ├── logs.js     # Log management functionality
│       │   ├── legacy-tasks.js # Legacy task management
│       │   └── scheduler.js # New task scheduler
│       └── main.js         # Main entry point (80 lines)
├── templates/              # Flask HTML templates
│   └── index.html          # Dual-tab UI (old + new versions)
├── tasks/                  # Task scripts directory
│   ├── config.json         # Task configuration
│   ├── claude_endpoint_check.py # Claude endpoint check task
│   ├── test_task.py        # Test task script
│   ├── example_task_script.py # Example Python task
│   └── example_task_script.sh # Example shell task
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
- Main Flask application serving both old and new UIs
- Registers both legacy and new API blueprints
- Serves static files and templates
- Port 5001 for all web services

### API Blueprints
#### New Scheduler API (`api_blueprint.py`) - **USE FOR NEW FEATURES**
- Blueprint for `/api/scheduler/tasks/*` endpoints
- Configuration and logging APIs
- Modern task scheduling functionality

#### Legacy API (`legacy_api_blueprint.py`) - **DO NOT MODIFY**
- Blueprint for `/api/tasks/*` endpoints
- Old task management functionality
- Maintained for backward compatibility only

### Frontend Architecture (Modular JavaScript)
#### Core Modules (`static/js/core/`)
- **`state.js`** - Global state management with StateManager (95 lines)
- **`api.js`** - API requests, connection management, and health checks (150 lines)
- **`utils.js`** - Common utility functions and helpers (85 lines)
- **`ui.js`** - UI operations, messaging, and modal management (200 lines)

#### Feature Modules (`static/js/modules/`)
- **`logs.js`** - Log management for both old and new versions (280 lines)
- **`legacy-tasks.js`** - Legacy task management functionality (320 lines)
- **`scheduler.js`** - New task scheduler with CRUD operations (450 lines)

#### Main Entry (`static/js/main.js`)
- Coordinated initialization and global event handling (80 lines)
- Module loading and compatibility layer
- Event binding and cleanup management

### Scheduling Services
#### Main Login Service (`auto_login.py`)
- Entry point for scheduled login automation
- APScheduler configuration and management
- Signal handling for graceful shutdown
- Environment validation

#### Generic Scheduler (`scheduler_engine.py`) - **NEW VERSION**
- Generic task scheduling engine
- Cron-based task management
- Can run standalone for testing
- Modern scheduling architecture

#### Legacy Task Manager (`task_manager.py`) - **OLD VERSION - DO NOT MODIFY**
- Legacy process management
- Old task lifecycle management
- Maintained for compatibility only

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

#### Process Manager (`process_manager.py`)
- Process creation and monitoring
- Process status management
- Resource usage statistics
- Process termination and cleanup

#### Logger Helper (`logger_helper.py`)
- Logging configuration
- Log reading and filtering
- Log formatting

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