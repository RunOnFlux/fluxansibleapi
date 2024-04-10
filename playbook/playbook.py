# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

from ansible_runner import run_command
from config.config import ALLOWED_TAGS, FLUX_PLAYBOOK_PATH, WORKING_DIR
from thread_tracker.tracker import event_tracker, pattern_tracker, Command, event_tracker_lock, pattern_tracker_lock, delete_pattern
from logger.logs import setup_logger

import sys
import time
import os

logger = setup_logger()

def run_playbook(tracker_event_id):
    
    # Quick check to make sure we are tracking this command
    if not (event_tracker.__contains__(tracker_event_id)):
        return

    # Get the command from the tracker
    command = event_tracker.get(tracker_event_id, Command(None, None))

    logger.info("Setting tracker to started: Inventory: %s, Tag: %s, ID: %s", command.pattern, command.tag, tracker_event_id)

    # Check the command against allowed tags
    if command.tag in ALLOWED_TAGS:
        # Set the status of the pattern to the tracker_event_id
        pattern_tracker_lock.acquire()
        pattern_tracker[command.pattern] = (tracker_event_id, command.tag)
        pattern_tracker_lock.release()

        # TODO - Figure out is this is the right way to do this
        # Change the current working directory to the desired directory
        # This might break things if dockerized, so keep an eye on this
        os.chdir(WORKING_DIR)

        command.result.output, command.result.error, command.result.rc = run_command(
        executable_cmd='ansible-playbook',
        cmdline_args=[FLUX_PLAYBOOK_PATH, '-l', command.pattern, '-t', command.tag],
        #input_fd=sys.stdin,
        output_fd=sys.stdout,
        error_fd=sys.stderr,
        )
        
        logger.info("Return Code: %s", command.result.rc)
        logger.info("Output: %s", command.result.output)
        logger.info("Error: %s", command.result.error)

    logger.info("Setting tracker to completed: Inventory: %s, Tag: %s, ID: %s", command.pattern, command.tag, tracker_event_id)
    
    # Set the tracker event to set, and update timestamp
    event_tracker_lock.acquire()
    command.tracker_event.set()
    command.set_completed_time(time.time())
    event_tracker_lock.release()

    # Delete the pattern from pattern tracker once it is completed
    # so we can accept more commands from api for this pattern.
    # This function locks the pattern lock 
    delete_pattern(command.pattern)
    
    
    
    

