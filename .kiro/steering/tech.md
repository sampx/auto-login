# Technology Stack

## Core Technologies

- **Python 3.9**: Main programming language
- **Playwright**: Browser automation framework with Chromium
- **APScheduler**: Task scheduling library for cron-like functionality
- **Flask**: Web framework for optional configuration interface
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

# Run production container
./start.sh

# Run tests
./test.sh

# Start with web interface
./start_web_app.sh
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps

# Run directly
python auto_login.py

# Run web interface
python web_interface.py
```

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