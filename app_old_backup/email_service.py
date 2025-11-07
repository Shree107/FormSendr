from flask import render_template, current_app
from flask_mail import Message
from app import mail
import bleach
from threading import Thread
import logging

logger = logging.getLogger(__name__)

def send_async_email(app, msg):
    """
    Send email asynchronously in a separate thread
    
    Args:
        app: Flask application instance
        msg: Flask-Mail Message object
    """
    with app.app_context():
        try:
            mail.send(msg)
            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

def send_form_submission_email(recipient_email, form_data):
    """
    Send form submission email to the recipient (asynchronously)
    
    Args:
        recipient_email (str): Email address of the recipient
        form_data (dict): Form data to be included in the email
    """
    # Sanitize all string values in form_data
    sanitized_data = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            # Sanitize HTML content to prevent XSS
            sanitized_data[key] = bleach.clean(value, tags=[], attributes={}, strip=True)
        else:
            sanitized_data[key] = value
    
    # Render email templates
    html_body = render_template('email_template.html', form_data=sanitized_data)
    text_body = render_template('email_template.txt', form_data=sanitized_data)
    
    # Create email message
    subject = f"New Form Submission from {sanitized_data.get('name', 'a user')}"
    msg = Message(
        subject=subject,
        recipients=[recipient_email],
        html=html_body,
        body=text_body
    )
    
    try:
        # Send email asynchronously in a background thread
        app = current_app._get_current_object()
        thread = Thread(target=send_async_email, args=(app, msg))
        thread.start()
        return True, "Email is being sent"
    except Exception as e:
        logger.error(f"Failed to start email thread: {str(e)}")
        return False, str(e)
