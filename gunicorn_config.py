"""Gunicorn configuration file for production deployment"""

import multiprocessing
import os

# Server socket - Use PORT from environment or default to 5000
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Cap at 4 workers for free tier
worker_class = "sync"
worker_connections = 1000

# Timeout settings - increased to handle email sending
timeout = 120  # 2 minutes timeout
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "formsendr"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None
