"""
WSGI config for FormSendr API.

This module contains the WSGI application used by Gunicorn.
"""

import os
from app import create_app

# Create the Flask application instance
app = create_app(os.getenv('FLASK_ENV') or 'production')

# This allows Gunicorn to find the app instance
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
