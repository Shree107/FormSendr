# FormSendr API

FormSendr is a Flask-based API that accepts form submissions and forwards them to a specified email address.

## Features

- Accepts POST form submissions from any HTML form
- Sends form data to a specified email address using Gmail SMTP
- HTML and plain-text email templates
- CSRF protection
- Input sanitization
- Rate limiting (5 requests per minute, 100 per day per IP)
- Responsive success/error pages

## Prerequisites

- Python 3.8+
- Gmail account (for sending emails)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd formsendr-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and update with your settings:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your Gmail credentials and other settings.

## Configuration

Edit the `.env` file with your configuration:

```ini
# Gmail SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use App Password for Gmail
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Security
SECRET_KEY=your-secret-key
CSRF_SECRET_KEY=your-csrf-secret-key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=5
RATE_LIMIT_PER_DAY=100
```

### Gmail Setup

1. Enable 2-Step Verification on your Google Account
2. Generate an App Password for your application
3. Use the generated app password in the `MAIL_PASSWORD` field

## Running the Application

```bash
# Development
python wsgi.py

# Production (using waitress)
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
