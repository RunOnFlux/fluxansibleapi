import datetime

def timestamp_to_datestring(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%c')