# CLAUDE.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

Web Task Scheduler - A modern, unified task scheduling and automation system with a web-based management interface. Built with Python, Flask web interface, and modular JavaScript frontend. The system provides comprehensive task management capabilities through an intuitive web UI.

## Architecture

**Core Components:**
- `app.py` - The unified Flask web server, serving the task management UI and APIs
- `api_blueprint.py` - Modern scheduler API blueprint (`/api/scheduler/tasks/*`) and system APIs
- `scheduler_engine.py` - Generic task scheduling engine with cron-based scheduling and file monitoring
- `browser_handler.py` - Playwright-based browser automation for web tasks
- `email_notifier.py` - Email notification system for task alerts
- `logger_helper.py` - Centralized logging configuration and management

**Service Architecture:**
- **Web Layer**: Single Flask REST API + Modular frontend architecture (port 5001)
- **Process Layer**: Subprocess management with signal handling and process groups
- **Automation Layer**: Playwright browser automation (headless Chromium)
- **Scheduling Layer**: APScheduler for cron/interval triggers with configuration file monitoring
- **Notification Layer**: SMTP email alerts
- **Frontend Layer**: Modular JavaScript with state management and API abstraction

## Development Commands

### Docker Setup (Recommended)
```bash
# Build and run
cd docker
./build.sh                   # Build Docker image
./start_docker.sh            # Start the Docker container (runs web app)
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the web application
./start_web_app.sh           # Start unified web interface (http://localhost:5001)
# OR
python app.py                # Direct Python execution

# Test components
python -m pytest tests/      # Run all tests
python tests/test_scheduler.py # Test scheduler functionality
python tests/test_email_notifier.py # Test email notifications
```

### Task Development
```bash
# Task files are organized in tasks/ directory
# Each task has its own subdirectory with:
# - config.json (task configuration)
# - {task_id}.py or {task_id}.sh (task script)
# - Optional README.md (task documentation)

# Example task structure:
# tasks/
# ├── my-python-task/
# │   ├── config.json
# │   └── my-python-task.py
# └── my-shell-task/
#     ├── config.json
#     └── my-shell-task.sh
```

### Configuration

**Environment Variables (.env):**
- `WEB_PORT` - Web server port (default: 5001)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `TASK_CONFIG_MONITOR_TYPE` - File monitoring type (watchdog, polling)
- `TASK_CONFIG_POLLING_INTERVAL` - Polling interval in seconds (default: 10)
- `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENT` - SMTP settings for notifications
- `SMTP_SERVER`, `SMTP_PORT` - SMTP configuration

**Log Locations:**
- `logs/sys.log` - System logs
- `logs/task_{task_id}.log` - Individual task execution logs

## API Endpoints

**Scheduler API:**
- `GET /api/scheduler/tasks` - List all tasks.
- `POST /api/scheduler/tasks` - Create a new task.
- `GET /api/scheduler/tasks/<task_id>` - Get task details.
- `PUT /api/scheduler/tasks/<task_id>` - Update an existing task.
- `DELETE /api/scheduler/tasks/<task_id>` - Delete a task.
- `POST /api/scheduler/tasks/<task_id>/toggle` - Enable or disable a task.
- `POST /api/scheduler/tasks/<task_id>/execute` - Manually trigger a task execution.
- `POST /api/scheduler/tasks/<task_id>/run-once` - Run a task immediately, just once.
- `GET /api/scheduler/tasks/<task_id>/logs` - Get logs for a specific task.
- `POST /api/scheduler/tasks/<task_id>/logs/clear` - Clear logs for a specific task.

**System API:**
- `GET /api/config` - Get current system configuration.
- `POST /api/config` - Update system configuration.
- `POST /api/scheduler/validate-cron` - Validate a cron expression.


## Testing

**Test URLs:**
- Web UI: http://localhost:5001
- API: http://localhost:5001/api/scheduler/tasks

## Security Notes

- Never commit `.env` file (contains credentials).
- Uses app-specific email passwords.
- Browser automation runs in headless mode.
- Process isolation via subprocess + signal handling.
- Environment variable validation on startup.

## Web Interface

The project features a modern, unified task scheduling management interface:

**Frontend Structure:**
- **Template**: `web/templates/index.html` - Single-page application
- **Styles**: `web/static/css/main.css` - Modern CSS styling
- **JavaScript**: Modular architecture in `web/static/js/`
  - **Core modules**: State management, API handling, utilities, UI operations
  - **Feature modules**: Task scheduler, log management
  - **Main entry**: Coordinated initialization and event handling

**Key Features:**
- Real-time task status monitoring
- Live log viewing with auto-refresh
- Task creation wizard with validation
- Cron expression validation
- Environment variable management
- Responsive design for desktop and mobile

**Usage:**
1. Access the web interface at http://localhost:5001
2. Create tasks using the "新建任务" (New Task) button
3. Monitor task execution through the log viewer
4. Manage tasks with enable/disable, edit, and delete operations

## Development Guidelines

**Code Organization:**
- Follow modular architecture principles
- Separate concerns between frontend and backend
- Use transaction management for data integrity
- Implement proper error handling and logging

**Task Development:**
- Each task should be self-contained in its directory
- Include proper logging and error handling
- Use environment variables for configuration
- Follow the established naming conventions

**API Development:**
- Follow RESTful principles
- Include proper input validation
- Use consistent error response format
- Implement request deduplication where needed
