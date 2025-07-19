---
inclusion: always
---

# Product Overview

## Automated Website Login System

This is a scheduled automation system that performs automatic website logins and sends email notifications about login status. The system is designed to keep accounts active by logging in at specified intervals.

## Key Features

- **Scheduled Login**: Configurable monthly or minute-based scheduling using APScheduler
- **Browser Automation**: Uses Playwright with Chromium for reliable web automation
- **Email Notifications**: Sends success/failure notifications via SMTP
- **Docker Support**: Fully containerized with Docker for easy deployment
- **Web Task Manager**: Flask-based web interface for task management and configuration
- **Task Control**: Start, stop, and monitor tasks through the web interface
- **Log Viewing**: Real-time task execution log viewing
- **Configuration Management**: Modify system parameters through the web interface
- **Robust Error Handling**: Retry logic, timeout handling, and graceful cleanup

## Target Use Case

Primarily designed for keeping hosting accounts (like Serv00) active by performing scheduled logins to prevent account suspension due to inactivity.

## Configuration

All settings are managed through environment variables in `.env` file, including:
- Website credentials and URL
- Email notification settings
- Schedule configuration
- Retry parameters
- Logging levels

## Code Conventions

- **Error Handling**: All browser interactions must include proper error handling with retries
- **Logging**: Use the logger_helper module for all logging operations
- **Environment Variables**: All configurable parameters should be accessed via environment variables
- **Process Management**: Use the process_manager module for any process-related operations
- **Task Structure**: New tasks should follow the pattern established in existing task modules

## Architecture Patterns

- **Separation of Concerns**: Each module has a single responsibility
- **Configuration Externalization**: All settings stored in environment variables
- **Dependency Injection**: Components receive their dependencies rather than creating them
- **Event-Driven**: Use signals and events for inter-component communication
- **Graceful Shutdown**: All components must handle termination signals properly

## AI Assistant Language Requirements

- Reply to users in Chinese
- Write code comments and git commit messages in English
- Follow snake_case naming for functions and variables
- Follow PascalCase for class names
- Document all public functions with docstrings