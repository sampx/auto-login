---
inclusion: always
---

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