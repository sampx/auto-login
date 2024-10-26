# Automated Login System

This system automatically logs into a specified website on a schedule and sends email notifications about the login status.

## Setup Instructions

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install Docker and Docker Compose
4. Run `chmod +x start.sh`
5. Execute `./start.sh`

## Configuration

- Edit `.env` file to configure:
  - Website credentials
  - Email settings
  - Schedule timing
  - Retry parameters

## Monitoring

- Logs are stored in the `logs` directory
- View live logs: `docker-compose logs -f`
- Check container status: `docker ps`

## Troubleshooting

If you encounter issues:
1. Check the logs in the `logs` directory
2. Verify your credentials in `.env`
3. Ensure the website is accessible
4. Check your email settings

## Security Notes

- Never commit the `.env` file
- Use app-specific passwords for email
- Regularly update dependencies