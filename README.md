# FormSendr API

A secure and efficient Flask-based API for handling form submissions and sending email notifications.

## Features

- 🔒 Secure form submission handling with input validation
- ⚡ Rate limiting to prevent abuse
- ✉️ Email notifications for form submissions
- 🔄 Environment-based configuration
- 🛡️ Security headers and Content Security Policy (CSP)
- 🚀 Production-ready with Gunicorn
- 📦 Simple, flat project structure

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SMTP server credentials (e.g., Gmail, SendGrid, etc.)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/formsendr-api.git
   cd formsendr-api
   ```

2. **Set up a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your configuration.

5. **Run the development server**
   ```bash
   flask run
   ```

## Configuration

Create a `.env` file with the following variables:

```ini
# Application Settings
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development  # or 'production' for production
FLASK_DEBUG=True

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Security Settings
SESSION_COOKIE_SECURE=False  # Set to True in production with HTTPS
FORCE_HTTPS=False  # Set to True in production

# Rate Limiting
RATE_LIMIT_PER_DAY=100
RATE_LIMIT_PER_MINUTE=5
```

## API Endpoints

### `GET /ping`
- **Description**: Health check endpoint
- **Response**: `200 OK` with `pong`

### `POST /submit/<recipient_email>`
- **Description**: Submit a form
- **Headers**: `Content-Type: application/json`
- **Request Body**: JSON object with form data
- **Response**: JSON object with status and message

## Deployment

### Using Gunicorn
pip install waitress
waitress-serve --port=5000 wsgi:app
```

The API will be available at `http://localhost:5000`

## Usage

### HTML Form Example

```html
<form action="https://your-domain.com/send/recipient@example.com" method="POST">
    <input type="text" name="name" placeholder="Your Name" required>
    <input type="email" name="email" placeholder="Your Email" required>
    <textarea name="message" placeholder="Your Message" required></textarea>
    <button type="submit">Send Message</button>
</form>
```

### API Endpoints

- `POST /send/<recipient_email>` - Submit form data
- `GET /health` - Health check endpoint

## Rate Limiting

The API enforces rate limiting to prevent abuse:
- 5 requests per minute
- 100 requests per day (per IP address)

## Security

- CSRF protection
- Input sanitization
- Secure headers via Flask-Talisman
- Rate limiting
- Gmail SMTP with TLS

## License

MIT License - see the LICENSE file for details.
