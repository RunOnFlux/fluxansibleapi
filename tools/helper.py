import datetime


def timestamp_to_datestring(timestamp) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp).strftime("%c")
