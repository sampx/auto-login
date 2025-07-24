---
inclusion: always
---

# Technology Stack

## Core Technologies

- **Python 3.12**: Main programming language
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
cd docker
./build.sh

# Run the containerized application
./start_docker.sh

# Access web interface at http://localhost:5001
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (if using browser automation)
playwright install chromium
playwright install-deps

# Run the web application
./start_web_app.sh           # Start web interface (port 5001)
python app.py                # Direct Python execution

# Test components
python -m pytest tests/      # Run all tests
python tests/test_scheduler.py # Test scheduler functionality
python tests/test_email_notifier.py # Test email notifications
```

## Frontend Architecture

### Modular JavaScript Structure
- **Clean Architecture**: Modular design with clear separation of concerns
- **Zero Function Duplication**: Eliminated all duplicate function definitions
- **Unified State Management**: Centralized global variable management
- **Modern UI/UX**: Responsive design with real-time updates

### Core Modules (`web/static/js/core/`)
- **StateManager** (`state.js`): Global state and timer management
- **APIManager** (`api.js`): Unified API requests with auto-reconnection
- **Utils** (`utils.js`): Common utilities and helper functions
- **UIManager** (`ui.js`): UI operations, modals, and messaging

### Feature Modules (`web/static/js/modules/`)
- **LogsManager** (`logs.js`): Real-time log viewing and management
- **Scheduler** (`scheduler.js`): Task scheduling with full CRUD operations

## API Endpoints

### Task Management API
- `GET /api/scheduler/tasks` - List all tasks
- `POST /api/scheduler/tasks` - Create new task
- `GET /api/scheduler/tasks/<id>` - Get task details
- `PUT /api/scheduler/tasks/<id>` - Update task
- `DELETE /api/scheduler/tasks/<id>` - Delete task
- `POST /api/scheduler/tasks/<id>/toggle` - Enable/disable task
- `POST /api/scheduler/tasks/<id>/execute` - Execute task manually
- `POST /api/scheduler/tasks/<id>/run-once` - Run task once immediately
- `GET /api/scheduler/tasks/<id>/logs` - Get task logs
- `POST /api/scheduler/tasks/<id>/logs/clear` - Clear task logs

### System Configuration API
- `GET /api/config` - Get current system configuration
- `POST /api/config` - Update system configuration
- `POST /api/scheduler/validate-cron` - Validate cron expression

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

- Base image: `python:3.12-slim`
- Timezone: `Asia/Shanghai`
- Headless browser setup with required dependencies
- Volume mounting for configuration files and persistent data
- Web interface startup as default entry point
- Port 5001 exposed for web interface access
- Persistent storage for logs, tasks, and configuration
- Environment variable support for configuration