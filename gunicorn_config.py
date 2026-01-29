# Gunicorn configuration for handling large file processing
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
# For free tier, use 1 worker to avoid memory issues
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 1200  # 20 minutes timeout for very large file processing
keepalive = 5
graceful_timeout = 30  # Give workers 30 seconds to finish before killing

# Memory optimization
max_requests = 1000  # Restart workers after this many requests to prevent memory leaks
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pixelcleaner"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
# keyfile = None
# certfile = None

