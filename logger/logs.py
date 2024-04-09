# logger_setup.py

import os
import logging

def setup_logger():
    log_dir = './'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'info.log')
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    return logging.getLogger(__name__)
