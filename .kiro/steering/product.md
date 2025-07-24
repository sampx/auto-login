---
inclusion: always
---

# Scheduled Automation System

A modern, unified task scheduling and automation system for all kinds of tasks.

## Core Architecture

**Unified Web Server:**
- **`app.py`** - Main Flask web server serving the unified task management UI and APIs (port 5001)
- **`api_blueprint.py`** - Modern scheduler API blueprint (`/api/scheduler/tasks/*`) and core system APIs

**Service Components:**
- **`scheduler_engine.py`** - Generic task scheduling engine with cron-based scheduling
- **`browser_handler.py`** - Playwright-based browser automation
- **`email_notifier.py`** - Email notification system
- **`logger_helper.py`** - Centralized logging configuration and management

**Frontend Architecture (Modular JavaScript):**
- **Core Modules**: State management, API handling, utilities, UI operations
- **Feature Modules**: Logs management, scheduler functionality
- **Main Entry**: Coordinated initialization and global event handling

**Service Layers:**
- **Web Layer**: Single Flask REST API + Modern modular frontend architecture (port 5001)
- **Process Layer**: Subprocess management with signal handling and process groups
- **Automation Layer**: Playwright browser automation (headless Chromium)
- **Scheduling Layer**: APScheduler for cron/interval triggers with file monitoring
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

## Development Guidelines

### Architecture Principles
- **Unified System**: Single modern architecture using `scheduler_engine.py` + `api_blueprint.py`
- **Modular Frontend**: Clean separation between core modules and feature modules
- **Single Web Interface**: Unified task management interface at `web/templates/index.html`
- **RESTful API**: All endpoints follow `/api/scheduler/tasks/*` pattern

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