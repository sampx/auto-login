# AGENT.md

This file provides guidance to AI agent when working with code in this repository.

# Scheduled Automation Aystem

A scheduled automation system for all kinds of tasks.

## Core Architecture

**Unified Web Server:**
- **`app.py`** - Main Flask web server serving both old and new task management UIs and APIs (port 5001)
- **`legacy_api_blueprint.py`** - Blueprint for old task management API (`/api/tasks/*`) - LEGACY, avoid modifications
- **`api_blueprint.py`** - Blueprint for new scheduler API (`/api/scheduler/tasks/*`) and core APIs

**Service Components:**
- **`auto_login.py`** - Main scheduled login service with APScheduler
- **`scheduler_engine.py`** - NEW VERSION: Generic task scheduling engine for cron-based tasks
- **`task_manager.py`** - OLD VERSION: Legacy process management (DO NOT MODIFY)
- **`browser_handler.py`** - Playwright-based browser automation
- **`email_notifier.py`** - Email notification system

**Frontend Architecture (Modular JavaScript):**
- **Core Modules**: State management, API handling, utilities, UI operations
- **Feature Modules**: Logs management, legacy tasks, scheduler functionality
- **Main Entry**: Coordinated initialization and global event handling

**Service Layers:**
- **Web Layer**: Single Flask REST API + Modular frontend architecture (port 5001)
- **Process Layer**: Subprocess management with signal handling
- **Automation Layer**: Playwright browser automation (headless Chromium)
- **Scheduling Layer**: APScheduler for cron/interval triggers
- **Notification Layer**: SMTP email alerts
- **Frontend Layer**: Modular JavaScript with state management and API abstraction

## Code Standards

### Naming Conventions
- **Files/Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Environment Variables**: `UPPER_SNAKE_CASE`

### Required Patterns
- **Error Handling**: All browser operations must include retry logic and proper cleanup
- **Logging**: Use `logger_helper` module exclusively for all logging operations
- **Configuration**: Access all settings via environment variables, never hardcode
- **Process Management**: Use `process_manager` for any process-related operations
- **Graceful Shutdown**: Implement signal handlers for clean termination

### Module Responsibilities
- Each module has single responsibility
- Dependencies injected rather than created internally
- Event-driven communication between components
- Proper resource cleanup in all operations

## Version Management

**CRITICAL RULE: All new features MUST be implemented in NEW VERSION only**

- **OLD VERSION**: `task_manager.py` + `legacy_api_blueprint.py` (DO NOT MODIFY)
- **NEW VERSION**: `scheduler_engine.py` + `api_blueprint.py` (USE FOR ALL NEW FEATURES)
- **UI**: Both versions accessible via tabs in `templates/index.html`
- **APIs**: 
  - Legacy: `/api/tasks/*` 
  - New: `/api/scheduler/tasks/*`

## Development Guidelines

### Version Selection
- **Never modify OLD VERSION code** (`task_manager.py`, `legacy_api_blueprint.py`)
- **Always use NEW VERSION** for feature requests (`scheduler_engine.py`, `api_blueprint.py`)
- Web interface contains two tabs - do not confuse them when making changes

### Browser Automation
- Always use Playwright with Chromium
- Include timeout handling for all page interactions
- Implement retry mechanisms for network operations
- Clean up browser resources in finally blocks

### Task Development
- Follow existing task patterns in `tasks/` directory
- Include proper status reporting and logging
- Handle both success and failure scenarios
- Provide meaningful error messages

### API Development
- RESTful endpoints for task management
- JSON responses with consistent error handling
- Proper HTTP status codes
- Input validation for all endpoints

### Configuration Management
- Environment variables in `.env` file (never commit)
- Required variables: `WEBSITE_URL`, `USERNAME`, `PASSWORD`, email settings
- Schedule configuration: `LOGIN_SCHEDULE_TYPE`, `LOGIN_SCHEDULE_DATE`, `LOGIN_SCHEDULE_TIME`
- Retry settings: `MAX_RETRIES` (1-10)

## Language Requirements
- **User Communication**: Chinese
- **Code Comments**: English
- **Git Commits**: English
- **Documentation**: English (except user-facing content)

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

# Technology Stack

## Core Technologies

- **Python 3.9**: Main programming language
- **Playwright**: Browser automation framework with Chromium
- **APScheduler**: Task scheduling library for cron-like functionality
- **Flask**: Web framework for unified web interface
- **Docker**: Containerization platform

## Key Dependencies

```
python-dotenv==1.0.0      # Environment variable management
webdriver_manager==3.8.6  # WebDriver management
playwright==1.48.0        # Browser automation
APScheduler==3.10.4       # Task scheduling
Flask==3.0.0              # Web interface
Flask-CORS==4.0.0         # Cross-origin resource sharing
psutil==5.9.5             # Process monitoring
watchdog==3.0.0           # File system monitoring
```

## Build System & Commands

### Docker Commands
```bash
# Build the Docker image
./build.sh

# Run scheduled login service
./start.sh

# Run unified web interface (port 5001)
./start_web_app.sh

# Run tests
./test.sh
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps

# Run services
python auto_login.py         # CLI scheduled service
python app.py                # Unified Web UI (http://localhost:5001)
python scheduler_engine.py   # Generic task scheduler (standalone testing)

# Test components
python test_login.py         # Test browser automation
python test_email_notifier.py # Test email notifications
python test_scheduler.py     # Test generic task scheduler
python -m pytest test_*.py   # Run all tests
```

## Frontend Architecture

### Modular JavaScript Structure
- **Total Code Reduction**: From 1779 lines (2 files) to 1660 lines (8 modular files)
- **Zero Function Duplication**: Eliminated all duplicate function definitions
- **Unified State Management**: Centralized global variable management
- **Backward Compatibility**: 100% compatible with existing HTML onclick handlers

### Core Modules (`static/js/core/`)
- **StateManager** (`state.js`): Global state and timer management
- **APIManager** (`api.js`): Unified API requests with auto-reconnection
- **Utils** (`utils.js`): Common utilities and helper functions
- **UIManager** (`ui.js`): UI operations, modals, and messaging

### Feature Modules (`static/js/modules/`)
- **LogsManager** (`logs.js`): Log viewing and management for both versions
- **LegacyTasks** (`legacy-tasks.js`): Old version task management
- **Scheduler** (`scheduler.js`): New version task scheduling with CRUD operations

## API Endpoints

### Legacy API (DO NOT MODIFY)
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/<id>` - Get task details
- `POST /api/tasks/<id>/start` - Start task
- `POST /api/tasks/<id>/stop` - Stop task
- `GET /api/tasks/<id>/status` - Get task status

### New Scheduler API (USE FOR NEW FEATURES)
- `GET /api/scheduler/tasks` - List scheduler tasks
- `POST /api/scheduler/tasks` - Create new task
- `GET /api/scheduler/tasks/<id>` - Get task details
- `PUT /api/scheduler/tasks/<id>` - Update task
- `DELETE /api/scheduler/tasks/<id>` - Delete task

### Configuration & Logging
- `GET /api/config` - Get current config
- `POST /api/config` - Update configuration
- `GET /api/logs/<task_id>` - Get task logs

## Environment Configuration

- **Production**: Uses `.env` file
- **Testing**: Uses `.env.test` file
- **Example**: `.env.example` provides template

## Logging

- Uses Python's built-in logging module
- Configurable log levels via `LOG_LEVEL` environment variable
- Logs stored in `logs/` directory with task-specific files
- Structured logging with timestamps and log levels
- Centralized logging configuration through `logger_helper.py`

## Docker Configuration

- Base image: `python:3.9-slim`
- Timezone: `Asia/Shanghai`
- Headless browser setup with required dependencies
- Volume mounting for configuration files
- Default startup changed to web interface
- Port 5001 exposed for web interface access
- Persistent storage for logs and configuration