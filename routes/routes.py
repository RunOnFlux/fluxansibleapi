# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

from flask import jsonify, request
from playbook.playbook import run_playbook
from thread_tracker.tracker import event_tracker, threads, is_pattern_running, get_pattern_id, Command, event_tracker_lock
from config.config import ALLOWED_PATTERNS, ALLOWED_TAGS
from logger.logs import setup_logger
from tools.helper import timestamp_to_datestring

import threading
import uuid
import time, datetime

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
    255: "Unknown error, per TQM"
}

# Default call
def base():
    return jsonify({"message": "This is a whitelisted API endpoint with API key authentication"}), 200

# Send command function that creates threaded call to ansible-playbook
def sendcommand():
    # Get the required data from the api call
    data = request.get_json()
    if 'pattern' not in data:
        return jsonify({"error": "Pattern not provided"}), 400

    if 'tags' not in data:
        return jsonify({"error": "Tags not provided"}), 400
    
    pattern = data['pattern']
    tags = data['tags']

    # Check to see if this pattern is already running an ansible command
    # If so, we don't want to run another command and screw up the node
    if(is_pattern_running(pattern)):
        pattern_event_id, pattern_tags = get_pattern_id(pattern)
        pattern_command = event_tracker.get(pattern_event_id, Command(None, None))
        return jsonify(
            {
                "status": "failed",
                "message": "Pattern is busy executing another command",
                "tracker_event_id": pattern_event_id,
                "tags": pattern_tags,
                "ansible_started_time": timestamp_to_datestring(pattern_command.started_timestamp)
            }
        )

    if (pattern not in ALLOWED_PATTERNS):
        return jsonify({"error": "Pattern not whitelisted"}), 400
    
    if (tags not in ALLOWED_TAGS):
        return jsonify({"error": "Tag not whitelisted"}), 400

    # Create the command object
    command = Command(pattern, tags)

    # Create an event to track the thread's completion
    command.set_tracker_event = threading.Event()

    # Generate a unique identifier for the tracker event
    tracker_event_id = str(uuid.uuid4())

    # Get the current time
    timestamp = time.time()

    # Set the time in the command
    command.set_start_time(timestamp)

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
            "tags": tags,
            "pattern": pattern,
            "ansible_started_time": timestamp_to_datestring(timestamp)
        }
    )

# Function to fetch the status of a current job id
def checkstatus():

    # Fetch the required data
    data = request.get_json()
    if 'tracker_event_id' not in data:
        return jsonify({"error": "Tracker event ID not provided"}), 400

    tracker_event_id = data['tracker_event_id']

    # Get the command if we have it 
    command = event_tracker.get(tracker_event_id, Command(None, None))
   
    # If we have the command, report our status
    if not command.is_null():
        if command.tracker_event.is_set():
            rc_message = 'default message'
            if command.result.rc in ANSIBLE_RETURN_CODES:
                rc_message = ANSIBLE_RETURN_CODES.get(command.result.rc)
            return jsonify(
                {
                    "status": "completed",
                    "ansible_started_time": timestamp_to_datestring(command.started_timestamp),
                    "ansible_completed_time": timestamp_to_datestring(command.completed_timestamp),
                    "tag": command.tag,
                    "pattern": command.pattern,
                    "result": command.result.output,
                    "ansible_return_code": command.result.rc,
                    "ansible_return_code_message": rc_message
                }
            )
        else:
            return jsonify(
                {
                    "status": "running",
                    "ansible_started_time": timestamp_to_datestring(command.started_timestamp),
                    "tag": command.tag,
                    "pattern": command.pattern,
                }
            )
    else:
        return jsonify({"error": "Tracker event not found"}), 400

