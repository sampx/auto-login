# AGENT.md

This file provides guidance to AI agent when working with code in this repository.

## Project Overview

Automated Login System that performs scheduled website logins with email notifications. Built with Python, Flask web interface, and Playwright browser automation.

## Architecture

**Core Components:**
- `auto_login.py` - Main scheduled login service with APScheduler
- `web_interface.py` - Flask web UI for task management and configuration (OLD VERSION)
- `browser_handler.py` - Playwright-based browser automation
- `task_manager.py` - Process management for login tasks (OLD VERSION)
- `email_notifier.py` - Email notification system (success/failure alerts)
- `scheduler_engine.py` - Generic task scheduling engine for cron-based tasks (NEW VERSION)
- `scheduler_api.py` - REST API for new task scheduler (NEW VERSION)

**Version Information:**
- **OLD VERSION**: `task_manager.py` + `web_interface.py` (legacy task management)
- **NEW VERSION**: `scheduler_engine.py` + `scheduler_api.py` (new task scheduler)
- **UI**: Both versions accessible via tabs in `templates/index.html`
- **Guideline**: All new feature requests should be implemented in the NEW VERSION only， !!! DO NOT CHANGE THE OLD VERSON TASK MANAGER'S CODE !!!

**Service Architecture:**
- **Web Layer**: Flask REST API + Static frontend (port 5001)
- **Process Layer**: Subprocess management with signal handling and process groups
- **Automation Layer**: Playwright browser automation (headless Chromium)
- **Scheduling Layer**: APScheduler for cron/interval triggers
- **Notification Layer**: SMTP email alerts

## Development Commands

### Docker Setup
```bash
# Build and run
./build.sh                    # Build Docker image
./start.sh                    # Start scheduled login service
./start_web_app.sh           # Start Flask web interface (port 5001)

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
python auto_login.py         # CLI scheduled service
python web_interface.py      # Web UI (http://localhost:5001)
python scheduler_engine.py   # Generic task scheduler

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
- `logs/task_auto_login.log` - Task execution logs

## API Endpoints

**Task Management:**
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/<id>` - Get task details
- `POST /api/tasks/<id>/start` - Start task
- `POST /api/tasks/<id>/stop` - Stop task
- `GET /api/tasks/<id>/status` - Get task status

**Configuration:**
- `GET /api/config` - Get current config
- `POST /api/config` - Update configuration
- `GET /api/logs/<task_id>` - Get task logs

## Testing

**Browser Tests:**
- `test_login.py` - Validates login automation
- `test_email_notifier.py` - Validates email notifications
- `test_scheduler.py` - Tests generic task scheduler

**Test URLs:**
- Web UI: http://localhost:5001
- API: http://localhost:5001/api/tasks (OLD VERSION TASKMANAGER)
- API: http://localhost:5002/api/scheduler/tasks (NEW VERSION TASKSCHEDULER)


## Security Notes

- Never commit `.env` file (contains credentials)
- Uses app-specific email passwords
- Browser automation runs in headless mode
- Process isolation via subprocess + signal handling
- Environment variable validation on startup

## Web Interface Notes

- 记住,本项目web 界面包含两个标签页,一个是老版本的任务管理界面,另一个是新版本的任务调度引擎任务管理界面,都在 templates/index.html 里面,修改代码时不要混淆.