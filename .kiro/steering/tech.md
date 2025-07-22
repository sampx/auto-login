---
inclusion: always
---

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
psutil==5.9.5             # Process monitoring
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
- Logs stored in `logs/app.log`
- Structured logging with timestamps and log levels

## Docker Configuration

- Base image: `python:3.9-slim`
- Timezone: `Asia/Shanghai`
- Headless browser setup with required dependencies
- Volume mounting for configuration files
- Default startup changed to web interface
- Port 5001 exposed for web interface access
- Persistent storage for logs and configuration