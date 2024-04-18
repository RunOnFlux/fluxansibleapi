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
    if "CF-Connecting-IP" in request.headers:
        return request.headers["CF-Connecting-IP"]
    elif "X-Forwarded-For" in request.headers:
        # Split X-Forwarded-For header to get the original client IP address
        return request.headers["X-Forwarded-For"].split(",")[0]
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
    api_key_dict = API_KEYS.get(api_key)
    if client_ip != api_key_dict.get("whitelisted_ipaddress"):
        logger.info(f"Request Denied: Unauthorized IP address from: {client_ip}")
        return jsonify({"error": "Unauthorized IP address"}), 401

    # If request has data
    if request.data:
        data = request.get_json()
        if data:

            # Get the tag info from the request and config
            tag = data.get("tag")
            whitelisted_tags = api_key_dict.get("whitelisted_tags")

            # If all tags are whitelisted, we are good to skip the rest of the tag checks
            if "all" not in whitelisted_tags:

                # If tag was provided in request
                if tag:
                    if not whitelisted_tags:
                        logger.info(
                            f"Request Denied: Unauthorized Tag command: whitelist empty {client_ip}"
                        )
                        return (
                            jsonify({"error": "Unauthorized tag, whitelist empty"}),
                            401,
                        )

                    if tag not in whitelisted_tags:
                        logger.info(
                            f"Request Denied: Unauthorized Tag command: tag not in whitelist {client_ip}"
                        )
                        return (
                            jsonify(
                                {"error": "Unauthorized tag, tag not in whitelist"}
                            ),
                            401,
                        )

            # Get the pattern info from the request and config
            pattern = data.get("pattern")
            whitelisted_patterns = api_key_dict.get("whitelisted_patterns")

            # If all patterns are whitelisted, we are good to skip the rest of the pattern checks
            if "all" not in whitelisted_patterns:

                # If pattern was provided in request
                if pattern:
                    if not whitelisted_patterns:
                        logger.info(
                            f"Request Denied: Unauthorized Pattern command: whitelist empty {client_ip}"
                        )
                        return (
                            jsonify({"error": "Unauthorized Pattern, whitelist empty"}),
                            401,
                        )

                    if pattern not in whitelisted_patterns:
                        logger.info(
                            f"Request Denied: Unauthorized Pattern command: pattern not in whitelist {client_ip}"
                        )
                        return (
                            jsonify(
                                {
                                    "error": "Unauthorized pattern, pattern not in whitelist"
                                }
                            ),
                            401,
                        )


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
