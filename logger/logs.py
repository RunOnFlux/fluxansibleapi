# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger() -> logging.Logger:
    log_dir = "./"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "info.log")

    # RotatingFileHandler with maxBytes set to 1MB and keeping backup count to 3
    rotating_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[rotating_handler]  # Add the rotating handler
    )

    return logging.getLogger(__name__)
