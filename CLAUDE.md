# AGENT.md

This file provides guidance to AI agent when working with code in this repository.

## Project Overview

Automated Login System that performs scheduled website logins with email notifications. Built with Python, Flask web interface, and Playwright browser automation. The system has been refactored to use a unified, modern task scheduling engine.

## Architecture

**Core Components:**
- `app.py` - The unified Flask web server, serving the task management UI and APIs.
- `api_blueprint.py` - Blueprint for the scheduler API (`/api/scheduler/tasks/*`) and other core APIs like configuration and logging.
- `scheduler_engine.py` - Generic task scheduling engine for cron-based tasks.
- `browser_handler.py` - Playwright-based browser automation.
- `email_notifier.py` - Email notification system (success/failure alerts).

**Service Architecture:**
- **Web Layer**: A single Flask REST API + Static frontend (port 5001) serving all endpoints.
- **Process Layer**: Subprocess management with signal handling and process groups.
- **Automation Layer**: Playwright browser automation (headless Chromium).
- **Scheduling Layer**: APScheduler for cron/interval triggers.
- **Notification Layer**: SMTP email alerts.

## Development Commands

### Docker Setup
```bash
# Build and run
./build.sh                    # Build Docker image
./start.sh                    # Start scheduled login service
./start_web_app.sh           # Start the unified Flask web interface (port 5001)

# Testing
./test.sh                     # Run all tests
python test_login.py         # Test browser automation
python test_email_notifier.py # Test email notifications
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run services
python app.py                # Unified Web UI (http://localhost:5001)
python scheduler_engine.py   # Generic task scheduler (can be run standalone for testing)

# Test components
python -m pytest test_*.py   # Run tests
```

### Configuration

**Environment Variables (.env):**
- `WEBSITE_URL` - Target login URL
- `USERNAME`, `PASSWORD` - Login credentials
- `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENT` - SMTP settings
- `SMTP_SERVER`, `SMTP_PORT` - SMTP configuration
- `LOGIN_SCHEDULE_TYPE` - 'monthly' or 'minutes'
- `LOGIN_SCHEDULE_DATE`, `LOGIN_SCHEDULE_TIME` - Cron schedule
- `MAX_RETRIES` - Retry attempts (1-10)

**Log Locations:**
- `logs/sys.log` - System logs
- `logs/task_*.log` - Task execution logs, where * is the task_id.

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

**Browser Tests:**
- `test_login.py` - Validates login automation.
- `test_email_notifier.py` - Validates email notifications.
- `test_scheduler.py` - Tests generic task scheduler.

**Test URLs:**
- Web UI: http://localhost:5001
- API: http://localhost:5001/api/scheduler/tasks

## Security Notes

- Never commit `.env` file (contains credentials).
- Uses app-specific email passwords.
- Browser automation runs in headless mode.
- Process isolation via subprocess + signal handling.
- Environment variable validation on startup.

## Web Interface Notes

- 记住, 本项目web界面现在是一个统一的、现代化的任务调度管理界面, 代码位于 `templates/index.html` 和 `static/js/` 目录下。
