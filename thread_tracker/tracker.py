# Copyright (c) 2024 Jeremy Anderson
# Copyright (c) 2024 Influx Technologies Limited
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.
from __future__ import annotations

import sched
import time
from dataclasses import dataclass, field
from threading import Event, Lock, Thread

from logger.logs import setup_logger

logger = setup_logger()

# Dictionary to store the status of each pattern
pattern_tracker: dict[str, EventToTagMap] = {}

# Dictionary to stores all ansible threaded events
event_tracker: dict[str, Command] = {}

# List for all active threads
threads = []

# Create a scheduler so we can cleanup our trackers
scheduler = sched.scheduler(time.time, time.sleep)
scheduler_thread = None

# Create Locks
pattern_tracker_lock = Lock()
event_tracker_lock = Lock()


# ToDo: name this properly
@dataclass
class EventToTagMap:
    event_id: str
    tag: str


@dataclass
class Result:
    output: str = ""
    error: str = ""
    rc: str = ""


@dataclass
class Command:
    """Stores tracking information for ansible commands"""

    pattern: str
    tag: str
    completed_timestamp: float = 0
    status: int = 0
    started_timestamp : float = field(default_factory=time.time)
    tracker_event : Event = field(default_factory=Event)
    result : Result = field(default_factory=Result)

    def __str__(self) -> str:
        return f"Pattern: {self.pattern}, Tag: {self.tag}, IsSet: {self.tracker_event.is_set()}, started: {self.started_timestamp}, completed: {self.completed_timestamp}"

    def __bool__(self) -> bool:
        return bool(self.pattern and self.tag)

    def set_start_time(self, started_time: float):
        self.started_timestamp = started_time

    def set_completed_time(self, completed_time: float):
        self.completed_timestamp = completed_time

    def set_status(self, status: int):
        self.status = status

def is_pattern_running(pattern: str) -> bool:
    """Checks pattern_tracker for a pattern"""
    with pattern_tracker_lock:
        response = pattern in pattern_tracker

    return response


def get_pattern_id(pattern: str) -> EventToTagMap | None:
    """Fetch the data from the pattern_tracker"""
    with pattern_tracker_lock:
        map = pattern_tracker.get(pattern, None)

    return map


def delete_tracker(tracker_event_id: str) -> None:
    """Delete tracker funciton. This function acquires locks"""
    with event_tracker_lock:
        if tracker_event_id in event_tracker:
            del event_tracker[tracker_event_id]


def delete_pattern(pattern: str) -> None:
    """Delete pattern function. This function acquires locks"""
    with pattern_tracker_lock:
        if pattern in pattern_tracker:
            del pattern_tracker[pattern]


def delete_old_trackers() -> None:
    current_time = time.time()
    trackers_to_delete = []
    patterns_to_delete = []

    # Lock the dictionaries
    with event_tracker_lock, pattern_tracker_lock:
        # Loop through all trackers and if the event has been set, it means it has been completed
        # If it has been 1 hour and it has been completed queue it for deletion
        for tracker_event_id, command in event_tracker.items():
            if (
                command.tracker_event.is_set()
                and (current_time - command.completed_timestamp) > 3600
            ):
                trackers_to_delete.append(tracker_event_id)

        # Patterns should automatically be deleted when the ansible job completes by
        # calling delete_pattern(command.pattern) in run_playbook function
        # This is a fall back just in case a pattern isn't deleted, so users aren't lock out
        # of calling new ansible commands to this pattern
        for pattern, eventToTagMap in pattern_tracker.items():
            if command := event_tracker.get(eventToTagMap.event_id, None):
                if command.tracker_event.is_set():
                    patterns_to_delete.append(pattern)

        # Delete the trackers that have been queued
        for tracker_event_id in trackers_to_delete:
            del event_tracker[tracker_event_id]

        # Delete the patterns that have been queued
        for pattern in patterns_to_delete:
            del pattern_tracker[pattern]

    # Reschedule the task to run again every 5 seconds
    scheduler.enter(10, 1, delete_old_trackers)


def schedule_task() -> None:
    scheduler.enter(10, 1, delete_old_trackers)
    scheduler.run()


def schedule_start() -> None:
    logger.info("Starting Scheduler")
    scheduler_thread = Thread(target=schedule_task)
    scheduler_thread.daemon = True
    scheduler_thread.start()


def cleanup() -> None:
    # Cancel all pending events in the scheduler
    for event in scheduler.queue:
        scheduler.cancel(event)

    # Wait for all threads to finish before exiting
    for thread in threads:
        thread.join()

    # Wait for the scheduler thread to finish
    if scheduler_thread:
        scheduler_thread.join()
