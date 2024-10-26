# Automated Login System

This system automatically logs into a specified website on a schedule and sends email notifications about the login status.

## Setup Instructions

1. Clone the repository and cd into it
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install Docker
4. Build docker image: `./build.sh`
5. Test the system: `./test.sh`
6. Run schedule: `./start.sh`

## Configuration

- Edit `.env` file to configure:
  - Website credentials
  - Email settings
  - Schedule timing
  - Retry parameters

## Build and Run

- Logs are stored in the `logs` directory
- Check container status: `docker ps`

## Security Notes

- Never commit the `.env` file
- Use app-specific passwords for email
- Regularly update dependencies