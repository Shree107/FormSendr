"""
Application factory for FormSendr API.

This module contains the application factory function.
"""

import os
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_mail import Mail

# Import blueprints and other components
from config import config

# Initialize extensions
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    limiter.init_app(app)
    mail.init_app(app)
    
    # Security headers
    Talisman(
        app,
        force_https=app.config.get('FORCE_HTTPS', True),
        strict_transport_security=True,
        session_cookie_secure=True,
        content_security_policy={
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                'https://cdn.jsdelivr.net',
                'https://code.jquery.com',
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
                'https: data:'
            ]
        }
    )
    
    # Apply rate limits from config
    limiter.limit(
        f"{app.config.get('RATE_LIMIT_PER_DAY', 100)} per day and "
        f"{app.config.get('RATE_LIMIT_PER_MINUTE', 5)} per minute"
    )
    
    # Import and register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Register error handlers
    from .errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)
    
    return app
