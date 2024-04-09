# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.


from flask import request, jsonify
from config.config import API_KEYS
from logger.logs import setup_logger

logger = setup_logger()

# Define a dictionary of API keys and their corresponding IP addresses
api_keys = API_KEYS

def authenticate_request():

    # Get the client's IP address
    client_ip = request.remote_addr

    logger.info('Received Request from: %s', str(client_ip))
    
    # Check if the client's IP address is in the allowed list for any API key
    authorized_ips = set(api_keys.values())
    if client_ip not in authorized_ips:
        return jsonify({"error": "Unauthorized IP address"}), 401
    
    # Check if the request contains a valid API key
    api_key = request.headers.get('X-API-Key')
    if api_key not in api_keys:
        return jsonify({"error": "Invalid API key"}), 401
