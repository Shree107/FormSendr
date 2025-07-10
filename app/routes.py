from flask import Blueprint, request, jsonify, render_template, url_for, redirect, current_app
from flask_limiter import RateLimitExceeded
from flask_mail import Message
from . import limiter, mail
from .email_service import send_form_submission_email
from .security import sanitize_input, validate_form_data, is_valid_email
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html')

@main.route('/docs')
def documentation():
    """Render the documentation page."""
    return render_template('docs.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    """Render the contact page and handle contact form submissions."""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            return render_template('contact.html', 
                                error="Please fill in all required fields.",
                                name=name, email=email, subject=subject, message=message)
        
        # Email validation
        is_valid, _ = is_valid_email(email)
        if not is_valid:
            return render_template('contact.html', 
                                error="Please enter a valid email address.",
                                name=name, email=email, subject=subject, message=message)
        
        try:
            # Send email (in a real app, you would implement this)
            # For now, we'll just log it
            logger.info(f"Contact form submission - Name: {name}, Email: {email}, Subject: {subject}, Message: {message}")
            
            # In a real app, you would uncomment and implement something like this:
            # msg = Message(
            #     subject=f"Contact Form: {subject}",
            #     sender=current_app.config['MAIL_DEFAULT_SENDER'],
            #     recipients=[current_app.config['CONTACT_EMAIL']],
            #     body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            # )
            # mail.send(msg)
            
            # Redirect to success page or show success message
            return render_template('contact.html', 
                                 success="Thank you for your message! We'll get back to you soon.")
            
        except Exception as e:
            logger.error(f"Error sending contact form: {str(e)}")
            return render_template('contact.html', 
                                error="An error occurred while sending your message. Please try again later.",
                                name=name, email=email, subject=subject, message=message)
    
    # For GET requests, just render the contact page
    return render_template('contact.html')

@main.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    """Handle rate limit exceeded errors"""
    return render_template('error.html', 
                         error_message="Rate limit exceeded. Please try again later."), 429

@main.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@main.route('/send/<recipient_email>', methods=['POST'])
@limiter.limit("5 per minute;100 per day")
def submit_form(recipient_email):
    """
    Handle form submissions and send emails
    
    Args:
        recipient_email (str): Email address of the recipient
    """
    try:
        # Validate recipient email
        is_valid, email_validation = is_valid_email(recipient_email)
        if not is_valid:
            logger.error(f"Invalid recipient email: {recipient_email}")
            return render_template('error.html', 
                               error_message="Invalid recipient email address"), 400
        
        # Get form data
        form_data = request.form.to_dict() or {}
        
        # If JSON data is sent, use that instead
        if request.is_json:
            form_data.update(request.get_json() or {})
        
        # Validate form data
        is_valid, errors = validate_form_data(form_data)
        if not is_valid:
            logger.error(f"Form validation failed: {errors}")
            return render_template('error.html', 
                               error_message="Invalid form data"), 400
        
        # Sanitize form data
        sanitized_data = sanitize_input(form_data)
        
        # Send email
        success, message = send_form_submission_email(recipient_email, sanitized_data)
        
        if success:
            logger.info(f"Email sent successfully to {recipient_email}")
            return render_template('success.html')
        else:
            logger.error(f"Failed to send email to {recipient_email}: {message}")
            return render_template('error.html', 
                               error_message="Failed to send email. Please try again later."), 500
    
    except Exception as e:
        logger.exception("An error occurred while processing the form submission")
        return render_template('error.html', 
                           error_message="An unexpected error occurred. Please try again later."), 500

# Error handlers
@main.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_message="Page not found"), 404

@main.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_message="Internal server error"), 500
