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

## AI Assistant Language Requirements

- Please always reply to the user in Chinese
- Comments in code and git commit messages should always be in English