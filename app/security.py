from flask_wtf.csrf import generate_csrf
from email_validator import validate_email, EmailNotValidError
import re

def is_valid_email(email):
    """Validate email format"""
    try:
        # Validate and normalize the email
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
        # Remove any potentially dangerous characters/scripts
        return re.sub(r'<[^>]*>?', '', input_data)
    return input_data

def generate_csrf_token():
    """Generate a CSRF token"""
    return generate_csrf()

def validate_form_data(form_data):
    """Validate form data"""
    errors = {}
    
    # Check for empty form data
    if not form_data:
        errors['form'] = 'No form data received'
        return False, errors
    
    # Check for suspiciously large form data (prevent DoS)
    if len(str(form_data)) > 10000:  # 10KB limit
        errors['form'] = 'Form data too large'
        return False, errors
    
    return True, {}
