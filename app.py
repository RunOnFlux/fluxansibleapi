# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

from flask import Flask
from flask_sslify import SSLify
from auth.authentication import authenticate_request
from thread_tracker.tracker import schedule_start, cleanup
from routes.routes import sendcommand, checkstatus, base
from logger.logs import setup_logger

import atexit

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

# Setup Authentication Checks (IP, Api-Keys)
app.before_request(authenticate_request)

# Routes
app.route('/api/', methods=['GET'])(base)
app.route('/api/sendcommand', methods=['POST'])(sendcommand)
app.route('/api/checkstatus', methods=['POST'])(checkstatus)

schedule_start()

# Register cleanup function to be called when the application exits
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(ssl_context=('./keys/host.cert', './keys/host.key'), debug=True)
