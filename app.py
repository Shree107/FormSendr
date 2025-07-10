"""
WSGI config for FormSendr API.

This module contains the WSGI application used by Django's development server.
"""

import os
from app import create_app

# Set the default configuration
app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == "__main__":
    # Run the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)
