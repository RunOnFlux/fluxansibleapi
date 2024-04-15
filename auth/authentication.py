# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.


from flask import Flask, Response, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.config import API_KEYS
from logger.logs import setup_logger

logger = setup_logger()

def get_client_ip():
    # Check if the request came through Cloudflare
    if 'CF-Connecting-IP' in request.headers:
        return request.headers['CF-Connecting-IP']
    elif 'X-Forwarded-For' in request.headers:
        # Split X-Forwarded-For header to get the original client IP address
        return request.headers['X-Forwarded-For'].split(',')[0]
    else:
        # If the headers are not present, return the remote address
        return request.remote_addr


def authenticate_request() -> Response:

    # Get the client's IP address
    client_ip = get_client_ip()

    logger.info(f"Received Request from: {client_ip}")

    # Check if the request contains a valid API key
    api_key = request.headers.get("X-API-Key")
    if api_key not in API_KEYS:
        logger.info(f"Request Denied: Invalid API key from: {client_ip}")
        return jsonify({"error": "Invalid API key"}), 401

    # Check if the client's IP address is in the allowed list for specific api key
    authorized_ips = set(API_KEYS.get(api_key))
    if client_ip not in authorized_ips:
        logger.info(f"Request Denied: Unauthorized IP address from: {client_ip}")
        return jsonify({"error": "Unauthorized IP address"}), 401


def setup_limiter(theapp: Flask, is_prod: bool) -> Limiter:
    memory_location = "memory://"

    if is_prod:
        # Redis connection URI
        memory_location = theapp.config["REDIS_SERVER_PROD"]

    return Limiter(
        get_remote_address,
        app=theapp,
        default_limits=["1000 per day", "100 per hour", "10 per minute"],
        storage_uri=memory_location,
    )
