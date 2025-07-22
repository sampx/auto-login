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
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── .env.example            # Environment template
├── .env                    # Production config (not in git)
├── .env.test               # Test configuration
├── logs/                   # Application logs
│   ├── sys.log             # System logs
│   ├── task_auto_login.log # Task execution logs
│   └── ...                 # Other task logs
├── static/                 # Static resource files
│   ├── css/                # CSS style files
│   └── js/                 # JavaScript files
├── templates/              # Flask HTML templates
│   └── index.html          # Dual-tab UI (old + new versions)
├── tasks/                  # Task scripts directory
└── .kiro/                  # Kiro configuration
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