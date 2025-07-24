# Web Task Scheduler

A modern, unified task scheduling and automation system with a web-based management interface. This system allows you to create, manage, and monitor scheduled tasks through an intuitive web UI.

## Features

- **Web-based Task Management**: Create, edit, delete, and monitor tasks through a modern web interface
- **Flexible Scheduling**: Support for cron expressions with validation
- **Real-time Monitoring**: Live log viewing and task status monitoring
- **Task Types**: Support for both Python and Shell script tasks
- **Environment Management**: Per-task environment variable configuration
- **Docker Support**: Containerized deployment for easy setup
- **File Monitoring**: Automatic task reloading when configuration files change

## Quick Start

### Using Docker (Recommended)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and Run**
   ```bash
   cd docker
   ./build.sh
   ./start_docker.sh
   ```

3. **Access Web Interface**
   - Open http://localhost:5001 in your browser
   - Start creating and managing your tasks

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Application**
   ```bash
   ./start_web_app.sh
   ```

## Configuration

Edit the `.env` file to configure:

- **Web Server**: `WEB_PORT` (default: 5001)
- **Logging**: `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)
- **Task Monitoring**: `TASK_CONFIG_MONITOR_TYPE` (watchdog, polling)
- **Email Settings**: SMTP configuration for notifications
- **Browser Automation**: Playwright settings for web automation tasks

## Project Structure

- **`web/`** - Web interface (HTML, CSS, JavaScript)
- **`tasks/`** - Task definitions and scripts
- **`logs/`** - Application and task execution logs
- **`docker/`** - Docker configuration files
- **`tests/`** - Test files and configurations

## Task Management

### Creating Tasks

1. Click "新建任务" (New Task) in the web interface
2. Fill in task details:
   - Task ID and name
   - Script type (Python/Shell)
   - Cron schedule expression
   - Timeout and retry settings
3. Configure environment variables if needed
4. Save and enable the task

### Task Configuration

Each task consists of:
- **Configuration file**: `tasks/{task_id}/config.json`
- **Script file**: `tasks/{task_id}/{task_id}.py` or `tasks/{task_id}/{task_id}.sh`
- **Logs**: `logs/task_{task_id}.log`

## API Endpoints

The system provides a RESTful API for task management:

- `GET /api/scheduler/tasks` - List all tasks
- `POST /api/scheduler/tasks` - Create new task
- `GET /api/scheduler/tasks/{id}` - Get task details
- `PUT /api/scheduler/tasks/{id}` - Update task
- `DELETE /api/scheduler/tasks/{id}` - Delete task
- `POST /api/scheduler/tasks/{id}/execute` - Execute task manually
- `POST /api/scheduler/tasks/{id}/toggle` - Enable/disable task

## Security Notes

- Never commit the `.env` file (contains sensitive configuration)
- Use app-specific passwords for email authentication
- Regularly update dependencies for security patches
- Review task scripts before execution
- Monitor logs for suspicious activity