from flask import Flask, render_template, request, jsonify, url_for, redirect, current_app, flash, abort
from urllib.parse import urlparse, urljoin
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect, generate_csrf
from email_validator import validate_email, EmailNotValidError
import bleach
import os
import re
import logging

# Initialize Flask app
app = Flask(__name__)

# Initialize CSRF Protection
csrf = CSRFProtect(app)

# Set secret key for CSRF
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

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

def format_html_email(form_data):
    """Format form data as a professional HTML email"""
    # Start building the HTML email
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
            .header { background-color: #4a6baf; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; border: 1px solid #ddd; border-top: none; }
            .field { margin-bottom: 15px; }
            .field-label { font-weight: bold; color: #555; margin-bottom: 5px; display: block; }
            .field-value { padding: 8px; background: #f9f9f9; border-radius: 4px; }
            .footer { margin-top: 20px; font-size: 12px; color: #777; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>New Form Submission</h2>
        </div>
        <div class="content">
    """
    
    # Add form fields
    for key, value in form_data.items():
        if key.lower() in ['_next', '_captcha', 'g-recaptcha-response', 'honeypot']:
            continue
            
        html += f"""
        <div class="field">
            <span class="field-label">{key.replace('_', ' ').title()}:</span>
            <div class="field-value">{value}</div>
        </div>
        """
    
    # Add footer
    html += """
        </div>
        <div class="footer">
            This email was sent from FormSendr. Please do not reply to this email.
        </div>
    </body>
    </html>
    """
    
    return html

def send_form_submission_email(recipient_email, form_data):
    """Send form submission email to the recipient"""
    try:
        # Sanitize and prepare form data
        sanitized_data = {}
        for key, value in form_data.items():
            if isinstance(value, str):
                sanitized_data[key] = bleach.clean(value, tags=[], attributes={}, strip=True)
            else:
                sanitized_data[key] = value
        
        # Get subject from form data or use default
        subject = sanitized_data.pop('_subject', 
                  sanitized_data.pop('subject', 
                  f"New Form Submission from {sanitized_data.get('name', 'a user')}"))
        
        # Prepare plain text version
        text_body = "New form submission received:\n\n"
        text_body += "\n".join(f"{k}: {v}" for k, v in sanitized_data.items())
        
        # Prepare HTML version
        html_body = format_html_email(sanitized_data)
        
        # Create and send email
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=text_body,
            html=html_body,
            sender=app.config.get('MAIL_DEFAULT_SENDER')
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

@app.after_request
def add_csrf_token(response):
    # Add CSRF token to response headers for AJAX requests
    response.headers['X-CSRFToken'] = generate_csrf()
    return response

@app.route('/send/<recipient_email>', methods=['POST'])
@app.route('/submit/<recipient_email>', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt  # Disable CSRF for external form submissions
def submit_form(recipient_email):
    """Handle form submissions and send emails"""
    try:
        # Get form data from both JSON and form submissions
        if request.is_json:
            form_data = request.get_json()
        else:
            # Handle both form data and URL-encoded data
            form_data = {}
            for key, values in request.form.lists():
                if len(values) == 1:
                    form_data[key] = values[0]
                else:
                    form_data[key] = values
            
            # Also check for JSON in the request body for API clients
            if not form_data and request.data:
                try:
                    form_data = request.get_json(force=True) or {}
                except:
                    pass
        
        # Log the received data for debugging
        logger.info(f"Received form data: {form_data}")
        
        # Validate form data
        is_valid, errors = validate_form_data(form_data)
        if not is_valid:
            logger.warning(f"Form validation failed: {errors}")
            if request.is_json:
                return jsonify({"status": "error", "message": "Invalid form data", "errors": errors}), 400
            else:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for('contact'))
        
        # Sanitize input
        form_data = sanitize_input(form_data)
        
        # Validate recipient email
        is_valid, email_error = is_valid_email(recipient_email)
        if not is_valid:
            logger.warning(f"Invalid recipient email: {recipient_email}")
            if request.is_json:
                return jsonify({"status": "error", "message": "Invalid recipient email", "error": email_error}), 400
            else:
                flash("Invalid recipient email address.", "error")
                return redirect(url_for('contact'))
        
        # Send email
        success, message = send_form_submission_email(recipient_email, form_data)
        if not success:
            logger.error(f"Failed to send email: {message}")
            if request.is_json:
                return jsonify({"status": "error", "message": "Failed to send email", "error": message}), 500
            else:
                flash("Failed to send message. Please try again later.", "error")
                return redirect(url_for('contact'))
        
        logger.info(f"Email sent successfully to {recipient_email}")
        
        # Handle redirect if _next parameter is provided
        next_url = form_data.get('_next')
        if next_url and is_safe_url(next_url):
            return redirect(next_url)
            
        # Return JSON response for API clients
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                "status": "success", 
                "message": "Form submitted successfully"
            }), 200
        else:
            # For direct form submissions, return a simple success page
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Form Submitted Successfully</title>
                <meta http-equiv="refresh" content="5;url=/" />
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success-message { color: #28a745; font-size: 24px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="success-message">✅ Form submitted successfully!</div>
                <p>You'll be redirected back in 5 seconds...</p>
                <p><a href="/">Click here</a> if you're not redirected automatically.</p>
            </body>
            </html>
            """
    
    except RateLimitExceeded:
        error_msg = "Rate limit exceeded. Please try again later."
        logger.warning(error_msg)
        if request.is_json:
            return jsonify({"status": "error", "message": error_msg}), 429
        else:
            flash(error_msg, "error")
            return redirect(url_for('contact'))
    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}", exc_info=True)
        error_msg = "An unexpected error occurred. Please try again later."
        if request.is_json:
            return jsonify({"status": "error", "message": error_msg}), 500
        else:
            flash(error_msg, "error")
            return redirect(url_for('contact'))

def is_safe_url(target):
    """Check if URL is safe for redirection"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

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
