from flask import render_template
from flask_mail import Message
from app import mail
import bleach

def send_form_submission_email(recipient_email, form_data):
    """
    Send form submission email to the recipient
    
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
    
    # Create and send email
    subject = f"New Form Submission from {sanitized_data.get('name', 'a user')}"
    msg = Message(
        subject=subject,
        recipients=[recipient_email],
        html=html_body,
        body=text_body
    )
    
    try:
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)
