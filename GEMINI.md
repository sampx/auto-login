# Gemini Project Analysis: auto-login

## Project Overview

This project is an automated task management system designed to handle web-based login processes. It utilizes a Selenium-based backend to perform the browser automation and provides a Flask-based web interface for users to configure, manage, and monitor these login tasks. The application is designed to be containerized using Docker, simplifying deployment and ensuring a consistent runtime environment. Key features include task scheduling, status monitoring, and email notifications.

## Core Technologies

- **Backend:** Python
- **Web Framework:** Flask
- **Web Automation:** Selenium
- **Containerization:** Docker
- **Frontend:** HTML, CSS, JavaScript

## Project Structure

The project is structured into several key components:

- `auto_login.py`: Contains the core logic for performing the automated login using Selenium.
- `web_interface.py`: A Flask application that serves the user interface, allowing for task management.
- `task_manager.py`: Manages the scheduling and execution of the defined login tasks.
- `browser_handler.py`: A helper module for initializing and managing the Selenium WebDriver.
- `email_notifier.py`: Handles sending email notifications regarding task status.
- `logger_helper.py`: Provides a centralized logging configuration for the application.
- `requirements.txt`: Lists all the Python dependencies required for the project.
- `Dockerfile`: Defines the instructions for building a Docker image of the application.
- `templates/` & `static/`: Contain the HTML templates and static assets (CSS, JS) for the Flask web interface.
- `*.sh` scripts (`build.sh`, `start.sh`, `test.sh`): Provide convenient scripts for building, running, and testing the application.

## Key Workflows

### Running the Application

To run the web application and the task manager, execute the main start script:

```bash
./start.sh
```

This script is typically responsible for launching the Flask web server (`web_interface.py`) and the background task processor (`task_manager.py`).

### Running with Docker

The application can also be built and run as a Docker container:

1.  **Build the image:**
    ```bash
    ./build.sh
    ```
    or
    ```bash
    docker build -t auto-login .
    ```

2.  **Run the container:**
    ```bash
    docker run -p 5000:5000 --env-file .env auto-login
    ```

### Running Tests

To execute the automated tests for the project, use the provided test script:

```bash
./test.sh
```

This will typically run tests defined in files like `test_login.py` and `test_email_notifier.py` using a test runner like `pytest` or `unittest`.

## Dependencies

All required Python packages are listed in the `requirements.txt` file. They can be installed using pip:

```bash
pip install -r requirements.txt
```
