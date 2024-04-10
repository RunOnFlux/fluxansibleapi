# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.


from flask import request, jsonify
from config.config import API_KEYS
from logger.logs import setup_logger

logger = setup_logger()

def authenticate_request():

    # Get the client's IP address
    client_ip = request.remote_addr

    logger.info('Received Request from: %s', str(client_ip))

    # Check if the request contains a valid API key
    api_key = request.headers.get('X-API-Key')
    if api_key not in API_KEYS:
        logger.info('Request Denied: Invalid API key from: %s', str(client_ip))
        return jsonify({"error": "Invalid API key"}), 401
    
    # Check if the client's IP address is in the allowed list for specific api key
    authorized_ips = set(API_KEYS.get(api_key))
    if client_ip not in authorized_ips:
        logger.info('Request Denied: Unauthorized IP address from: %s', str(client_ip))
        return jsonify({"error": "Unauthorized IP address"}), 401
    
    
