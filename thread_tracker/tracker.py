# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import threading
import time
import sched
from logger.logs import setup_logger
logger = setup_logger()

# Dictionary to store the status of each pattern
pattern_tracker = {}

# Dictionary to stores all ansible threaded events
event_tracker = {}

# List for all active threads
threads = []

# Create a scheduler so we can cleanup our trackers
scheduler = sched.scheduler(time.time, time.sleep)
scheduler_thread = None

# Create Locks
pattern_tracker_lock = threading.Lock()
event_tracker_lock = threading.Lock()

class Result:
    def __init__(self):
        self.output = ""
        self.error = ""
        self.rc = ""

# Command class
# Stores tracking information for ansible commands
class Command:
    def __init__(self, pattern, tag):
        self.pattern = pattern
        self.tag = tag
        self.tracker_event = threading.Event()
        self.started_timestamp = 0
        self.completed_timestamp = 0
        self.status = 0
        self.result = Result()
    
    def set_start_time(self, started_time):
        self.started_timestamp = started_time

    def set_completed_time(self, completed_time):
        self.completed_timestamp = completed_time

    def set_tracker_event(self, tracker_event):
        self.tracker_event = tracker_event

    def set_status(self, status):
        self.status = status

    def to_string(self):
        return f"Pattern: {self.pattern}, Tag: {self.tag}, IsSet: {self.tracker_event.is_set()}, started: {self.started_timestamp}, completed: {self.completed_timestamp}"

    def is_null(self):
        return self.pattern == None or self.tag == None

# Checks pattern_tracker for a pattern
def is_pattern_running(pattern):
    pattern_tracker_lock.acquire()
    response = pattern_tracker.__contains__(pattern)
    pattern_tracker_lock.release()
    return response

# Fetch the data from the pattern_tracker
def get_pattern_id(pattern):
    pattern_tracker_lock.acquire()
    id, tag = pattern_tracker.get(pattern, (None, None))
    pattern_tracker_lock.release()
    return id, tag

# Delete tracker funciton. This function acquires locks
def delete_tracker(tracker_event_id):
    event_tracker_lock.acquire()
    if tracker_event_id in event_tracker:
        del event_tracker[tracker_event_id]
    event_tracker_lock.release()

# Delete pattern function. This function acquires locks
def delete_pattern(pattern):
    pattern_tracker_lock.acquire()
    if pattern in pattern_tracker:
        del pattern_tracker[pattern]
    pattern_tracker_lock.release()

def delete_old_trackers():
    current_time = time.time()
    trackers_to_delete = []
    patterns_to_delete = []

    # Lock the dictionaries
    event_tracker_lock.acquire()
    pattern_tracker_lock.acquire()

    # Loop through all trackers and if the event has been set, it means it has been completed
    # If it has been 1 hour and it has been completed queue it for deletion
    for tracker_event_id, command in event_tracker.items():
        if command.tracker_event.is_set() and (current_time - command.completed_timestamp) > 3600:
            trackers_to_delete.append(tracker_event_id)

    # Patterns should automatically be deleted when the ansible job completes by
    # calling delete_pattern(command.pattern) in run_playbook function
    # This is a fall back just in case a pattern isn't deleted, so users aren't lock out
    # of calling new ansible commands to this pattern
    for pattern, (pattern_event_id, tags) in pattern_tracker.items():
        command = event_tracker.get(pattern_event_id, Command(None, None))
        if (command.pattern is not None):
            if (command.tracker_event.is_set()):
                patterns_to_delete.append(pattern)

    # Delete the trackers that have been queued
    for tracker_event_id in trackers_to_delete:
        del event_tracker[tracker_event_id]

    # Delete the patterns that have been queued
    for pattern in patterns_to_delete:
        del pattern_tracker[pattern]

    # Unlock the locks after we are done modifying the dictionaries
    event_tracker_lock.release()
    pattern_tracker_lock.release()

    # Reschedule the task to run again every 5 seconds
    scheduler.enter(10, 1, delete_old_trackers)

def schedule_task():
    scheduler.enter(10, 1, delete_old_trackers)
    scheduler.run()

def schedule_start():
    logger.info("Starting Scheduler")
    scheduler_thread = threading.Thread(target=schedule_task)
    scheduler_thread.daemon = True
    scheduler_thread.start()

def cleanup():
    # Cancel all pending events in the scheduler
    for event in scheduler.queue:
        scheduler.cancel(event)

    # Wait for all threads to finish before exiting
    for thread in threads:
        thread.join()

    # Wait for the scheduler thread to finish
    if scheduler_thread:
        scheduler_thread.join()


