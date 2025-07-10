from flask import Flask, render_template, request, jsonify, url_for, redirect, current_app
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_mail import Mail, Message
from email_validator import validate_email, EmailNotValidError
import bleach
import os
import re
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure the application
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    FLASK_ENV=os.getenv('FLASK_ENV', 'production'),
    DEBUG=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
    
    # Email configuration
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', 'true').lower() == 'true',
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', ''),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', ''),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', ''),
    
    # Security
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
    FORCE_HTTPS=os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
    
    # Rate limiting
    RATE_LIMIT_PER_DAY=int(os.getenv('RATE_LIMIT_PER_DAY', 100)),
    RATE_LIMIT_PER_MINUTE=int(os.getenv('RATE_LIMIT_PER_MINUTE', 5))
)

# Initialize extensions
mail = Mail(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{app.config['RATE_LIMIT_PER_DAY']} per day", 
                   f"{app.config['RATE_LIMIT_PER_MINUTE']} per minute"],
    storage_uri="memory://"  # For development only
)

# Security headers
Talisman(
    app,
    force_https=app.config['FORCE_HTTPS'],
    strict_transport_security=True,
    session_cookie_secure=app.config['SESSION_COOKIE_SECURE'],
    content_security_policy={
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            'https://cdn.jsdelivr.net',
            'https://code.jquery.com',
            "'unsafe-inline'"
        ],
        'style-src': [
            "'self'",
            'https://cdn.jsdelivr.net',
            'https://fonts.googleapis.com',
            "'unsafe-inline'"
        ],
        'font-src': [
            "'self'",
            'https://fonts.gstatic.com',
            'https://cdn.jsdelivr.net',
            'data:'
        ],
        'img-src': [
            "'self'",
            'data:',
            'https:'
        ]
    },
    content_security_policy_nonce_in=['script-src']
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security functions
def is_valid_email(email):
    """Validate email format"""
    try:
        valid = validate_email(email)
        return True, valid.email
    except EmailNotValidError as e:
        return False, str(e)

def sanitize_input(input_data):
    """Sanitize input data to prevent XSS and other attacks"""
    if isinstance(input_data, dict):
        return {k: sanitize_input(v) for k, v in input_data.items()}
    elif isinstance(input_data, list):
        return [sanitize_input(item) for item in input_data]
    elif isinstance(input_data, str):
        return re.sub(r'<[^>]*>?', '', input_data)
    return input_data

def validate_form_data(form_data):
    """Validate form data"""
    errors = {}
    if not form_data:
        errors['form'] = 'No form data received'
        return False, errors
    if len(str(form_data)) > 10000:  # 10KB limit
        errors['form'] = 'Form data too large'
        return False, errors
    return True, {}

def send_form_submission_email(recipient_email, form_data):
    """Send form submission email to the recipient"""
    sanitized_data = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            sanitized_data[key] = bleach.clean(value, tags=[], attributes={}, strip=True)
        else:
            sanitized_data[key] = value
    
    try:
        subject = f"New Form Submission from {sanitized_data.get('name', 'a user')}"
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=f"New form submission received:\n\n" + 
                 "\n".join(f"{k}: {v}" for k, v in sanitized_data.items())
        )
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False, str(e)

# Routes
@app.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html')

@app.route('/docs')
@app.route('/documentation')
def documentation():
    """Render the documentation page."""
    return render_template('docs.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Render the contact page and handle form submissions."""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, message]):
            return render_template('contact.html', 
                                error="Please fill in all required fields.",
                                name=name, email=email, message=message)
        
        # Email validation
        is_valid, _ = is_valid_email(email)
        if not is_valid:
            return render_template('contact.html', 
                                error="Please enter a valid email address.",
                                name=name, email=email, message=message)
        
        # Send email
        form_data = {'name': name, 'email': email, 'message': message}
        success, _ = send_form_submission_email(
            os.getenv('ADMIN_EMAIL', email),  # Send to admin or back to user
            form_data
        )
        
        if success:
            return render_template('contact.html', 
                                success="Thank you for your message! We'll get back to you soon.")
        else:
            return render_template('contact.html', 
                                error="Failed to send message. Please try again later.",
                                name=name, email=email, message=message)
    
    # GET request
    return render_template('contact.html')

@app.route('/ping')
def ping():
    """Health check endpoint."""
    return 'pong', 200

@app.route('/submit/<recipient_email>', methods=['POST'])
@limiter.limit("5 per minute")
def submit_form(recipient_email):
    """Handle form submissions and send emails"""
    try:
        # Get form data
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = request.form.to_dict()
        
        # Validate form data
        is_valid, errors = validate_form_data(form_data)
        if not is_valid:
            return jsonify({"status": "error", "message": "Invalid form data", "errors": errors}), 400
        
        # Sanitize input
        form_data = sanitize_input(form_data)
        
        # Validate recipient email
        is_valid, email_error = is_valid_email(recipient_email)
        if not is_valid:
            return jsonify({"status": "error", "message": "Invalid recipient email", "error": email_error}), 400
        
        # Send email
        success, message = send_form_submission_email(recipient_email, form_data)
        if not success:
            return jsonify({"status": "error", "message": "Failed to send email", "error": message}), 500
        
        return jsonify({"status": "success", "message": "Form submitted successfully"}), 200
    
    except RateLimitExceeded:
        return jsonify({"status": "error", "message": "Rate limit exceeded. Please try again later."}), 429
    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred"}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"status": "error", "message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

# Run the application
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
