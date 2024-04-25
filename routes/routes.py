# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import threading
import uuid

from flask import Response, jsonify, request

from config.config import (
    ALLOWED_PATTERNS,
    ALLOWED_TAGS,
    ALLOWED_PLAYBOOKS,
    ALLOW_DEFAULT_PLAYBOOK,
    DEFAULT_PLAYBOOK,
)
from logger.logs import setup_logger
from playbook.playbook import run_playbook
from thread_tracker.tracker import (
    Command,
    event_tracker,
    get_pattern_id,
    is_pattern_running,
    threads,
)
from tools.helper import timestamp_to_datestring

# Get the logger so we can log
logger = setup_logger()

ANSIBLE_RETURN_CODES = {
    0: "The command ran successfully, without any task failures or internal errors.",
    1: "There was a fatal error or exception during execution.",
    3: "Hosts unreachable",
    4: "Hosts unreachable",
    5: "Error with the options provided to the command",
    6: "Command line args are not UTF-8 encoded",
    8: "A condition called RUN_FAILED_BREAK_PLAY occurred within Task Queue Manager",
    99: "Ansible received a keyboard interrupt (SIGINT) while running the playbook- i.e. the user hits Ctrl+c during the playbook run",
    143: "Ansible received a kill signal (SIGKILL) during the playbook run- i.e. an outside process kills the ansible-playbook command.",
    250: "Unexpected exception- often due to a bug in a module, jinja templating errors, etc. (ref1)",
    255: "Unknown error, per TQM",
}


# Default call
def base() -> Response:
    return (
        jsonify(
            {
                "message": "This is a whitelisted API endpoint with API key authentication"
            }
        ),
        200,
    )


def sendcommand() -> tuple[Response, int]:
    """Send command function that creates threaded call to ansible-playbook"""
    # Get the required data from the api call
    data = request.get_json()

    # If ALLOW_DEFAULT_PLAYBOOK is set to False, playbook is required
    if not ALLOW_DEFAULT_PLAYBOOK:
        if "playbook" not in data:
            return jsonify({"error": "playbook required"}), 400

    if "pattern" not in data:
        return jsonify({"error": "Pattern not provided"}), 400

    if "tag" not in data:
        return jsonify({"error": "Tag not provided"}), 400

    playbook = data.get("playbook")  # Can be None
    pattern = data["pattern"]
    tag = data["tag"]
    extra_vars = data.get("extra_vars")

    # Check to see if this pattern is already running an ansible command
    # If so, we don't want to run another command and screw up the node
    if is_pattern_running(pattern):
        map = get_pattern_id(pattern)
        pattern_command = event_tracker.get(map.event_id, None)
        return jsonify(
            {
                "status": "failed",
                "message": "Pattern is busy executing another command",
                "tracker_event_id": map.event_id,
                "tag": map.tag,
                "ansible_started_time": timestamp_to_datestring(
                    pattern_command.started_timestamp
                ),
            }
        )

    if pattern not in ALLOWED_PATTERNS:
        return jsonify({"error": "Pattern not whitelisted"}), 400

    if tag not in ALLOWED_TAGS:
        return jsonify({"error": "Tag not whitelisted"}), 400

    playbook_path = ""
    playbook_name = ""

    if playbook:
        if playbook not in ALLOWED_PLAYBOOKS:
            return jsonify({"error": "Playbook not whitelisted"}), 400
        else:
            playbook_path = ALLOWED_PLAYBOOKS.get(playbook)
            playbook_name = playbook
    else:
        if ALLOW_DEFAULT_PLAYBOOK:
            playbook_path = DEFAULT_PLAYBOOK
            playbook_name = "default"
        else:
            return jsonify({"error": "Playbook not supported: default false"}), 400

    # Final check on playbook, if default was selected and happen to be set to "" we don't want to proceed
    if not playbook_path:
        logger.info("playbook path is empty string")
        return jsonify({"error": "Playbook not supported: default empty string"}), 400

    # If extra_vars wasn't included in the api call, it is None. So Set it to empty dict
    if not extra_vars:
        extra_vars = {}

    # Check if the extra_vars is a dictionary
    if not isinstance(extra_vars, dict):
        return jsonify({"error": "extra_vars must be a dictionary"}), 400

    # Create the command object
    command = Command(
        pattern=pattern,
        tag=tag,
        playbook_name=playbook_name,
        playbook_path=playbook_path,
        extra_vars=extra_vars,
    )

    # Generate a unique identifier for the tracker event
    tracker_event_id = str(uuid.uuid4())

    # Store the event object in the event_tracker dictionary along with its creation time
    event_tracker[tracker_event_id] = command

    # Spin up a new thread to execute the Ansible command
    thread = threading.Thread(target=run_playbook, args=[tracker_event_id])
    thread.start()

    # Keep track of the thread
    threads.append(thread)

    # Return a response indicating that the Ansible command execution has started
    return jsonify(
        {
            "status": "started",
            "message": "Ansible command execution started.",
            "tracker_event_id": tracker_event_id,
            "tag": tag,
            "pattern": pattern,
            "playbook": playbook_name,
            "ansible_started_time": timestamp_to_datestring(command.started_timestamp),
        }
    )


# Function to fetch the status of a current job id
def checkstatus() -> tuple[Response, int]:

    # Fetch the required data
    data = request.get_json()
    if "tracker_event_id" not in data:
        return jsonify({"error": "Tracker event ID not provided"}), 400

    tracker_event_id = data["tracker_event_id"]

    # Get the command if we have it
    command = event_tracker.get(tracker_event_id, None)

    # If we have the command, report our status
    if not command:
        return jsonify({"error": "Tracker event not found"}), 400

    if command.tracker_event.is_set():
        rc_message = "default message"
        if command.result.rc in ANSIBLE_RETURN_CODES:
            rc_message = ANSIBLE_RETURN_CODES.get(command.result.rc)
        return (
            jsonify(
                {
                    "status": "completed",
                    "ansible_started_time": timestamp_to_datestring(
                        command.started_timestamp
                    ),
                    "ansible_completed_time": timestamp_to_datestring(
                        command.completed_timestamp
                    ),
                    "tag": command.tag,
                    "pattern": command.pattern,
                    "playbook": command.playbook_name,
                    "result": command.result.output,
                    "ansible_return_code": command.result.rc,
                    "ansible_return_code_message": rc_message,
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "running",
                    "ansible_started_time": timestamp_to_datestring(
                        command.started_timestamp
                    ),
                    "tag": command.tag,
                    "pattern": command.pattern,
                    "playbook": command.playbook_name,
                }
            ),
            200,
        )
