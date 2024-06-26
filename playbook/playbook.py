# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import os
import sys
import time
import json

from ansible_runner import run_command

from config.config import ALLOWED_TAGS, FLUX_PLAYBOOK_PATH, WORKING_DIR
from logger.logs import setup_logger
from thread_tracker.tracker import (
    EventToTagMap,
    delete_pattern,
    event_tracker,
    event_tracker_lock,
    pattern_tracker,
    pattern_tracker_lock,
)

logger = setup_logger()


def run_playbook(tracker_event_id: str):
    # Get the command from the tracker
    command = event_tracker.get(tracker_event_id, None)

    if not command:
        return

    logger.info(
        f"Setting tracker to started: Inventory: {command.pattern}, Tag: {command.tag}, ID: {tracker_event_id}",
    )

    # Check the command against allowed tags
    if command.tag in ALLOWED_TAGS:
        # Set the status of the pattern to the tracker_event_id
        with pattern_tracker_lock:
            # This shouldn't happen: but we better double check there wasn't a race condition that
            # allowed pattern to be started while this command was being parsed
            # Even though this shouldn't happen, it is important to have redudency
            if pattern_tracker.get(command.pattern, None):
                logger.info(
                    f"Pattern was found running already. Stopping Command: Inventory: {command.pattern}, Tag: {command.tag}, ID: {tracker_event_id}"
                )
                return

            pattern_tracker[command.pattern] = EventToTagMap(
                tracker_event_id, command.tag
            )

        extra_vars_json = json.dumps(command.extra_vars)

        command.result.output, command.result.error, command.result.rc = run_command(
            executable_cmd="ansible-playbook",
            host_cwd=WORKING_DIR,
            cmdline_args=[
                command.playbook_path,
                "-l",
                command.pattern,
                "-t",
                command.tag,
                "--extra-vars",
                extra_vars_json,
            ],
            # input_fd=sys.stdin,
            output_fd=sys.stdout,
            error_fd=sys.stderr,
        )

        logger.info(
            f"Return Code: {command.result.rc}",
        )
        logger.info(f"Output: {command.result.output}")
        logger.info(f"Error: {command.result.error}")

    logger.info(
        f"Setting tracker to completed: Inventory: {command.pattern}, Tag: {command.tag}, ID: {tracker_event_id}",
    )

    # Set the tracker event to set, and update timestamp
    with event_tracker_lock:
        command.tracker_event.set()
        command.set_completed_time(time.time())

    # Delete the pattern from pattern tracker once it is completed
    # so we can accept more commands from api for this pattern.
    # This function locks the pattern lock
    delete_pattern(command.pattern)
