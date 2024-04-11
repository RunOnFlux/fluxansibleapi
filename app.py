# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import atexit
import os

from flask import Flask
from flask_sslify import SSLify

from auth.authentication import authenticate_request, setup_limiter
from logger.logs import setup_logger
from routes.routes import base, checkstatus, sendcommand
from thread_tracker.tracker import cleanup, schedule_start


# Graceful shutdown hook for Gunicorn
def on_exit(server):
    print("Shutting down...")
    cleanup()

# Register the exit hook with Gunicorn
def post_fork(server, worker):
    server.log.info("Adding shutdown hook")
    worker.init_signal = lambda: None
    worker.log.info("Adding shutdown hook")
    worker.wsgi = lambda *args, **kwargs: None
    worker.log.info("Adding shutdown hook")
    worker.cfg.worker_exit = on_exit
    worker.log.info("Adding shutdown hook")

app = Flask(__name__)
sslify = SSLify(app)
logger = setup_logger()
app.config.from_pyfile('config/config.py')

# Ensure ENV is set to 'production' when running with Gunicorn
if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
    if app.config.get('ENV') != 'production':
        raise ValueError("ENV configuration variable must be set to 'production' when running with Gunicorn.")


# Setup the api rate limiter
limiter = setup_limiter(app, app.config['ENV'] == 'production')

# Setup Authentication Checks (IP, Api-Keys)
app.before_request(authenticate_request)

# Routes
# Apply limiter to route functions
@app.route('/api/', methods=['GET'])
@limiter.limit("10 per minute")  # Limiting to 10 requests per minute
def base_route():
    return base()

@app.route('/api/sendcommand', methods=['POST'])
@limiter.limit("50 per minute")  # Limiting to 50 requests per minute
def sendcommand_route():
    return sendcommand()

@app.route('/api/checkstatus', methods=['POST'])
@limiter.limit("50 per minute")  # Limiting to 50 requests per minute
def checkstatus_route():
    return checkstatus()

# Start the scheduler
schedule_start()

# Register cleanup function to be called when the application exits
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(ssl_context=('./keys/host.cert', './keys/host.key'), debug=True)
