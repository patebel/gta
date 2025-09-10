import datetime
from datetime import datetime

from util.logging import log_error


class Timer:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = datetime.now()

    def stop(self):
        end_time = datetime.now()
        return seconds_to_hhmm((end_time - self.start_time).seconds)


def time_to_seconds(time_str):
    try:
        if time_str and ("AM" in time_str or "PM" in time_str):
            time_str = time_str.replace(" AM", "").replace(" PM", "")
            hours, minutes = map(int, time_str.split(':'))
            if "PM" in time_str:
                hours += 12
        else:
            hours, minutes = map(int, time_str.split(':'))
        return hours * 3600 + minutes * 60
    except ValueError:
        log_error(f"Invalid time format: {time_str}", )
        return None


def seconds_to_hhmm(seconds, round_to=0):
    total_minutes = seconds // 60

    if round_to > 0:
        rounding_factor = round_to / 2
        total_minutes = (total_minutes + rounding_factor) // round_to * round_to

    hours = total_minutes // 60
    minutes = total_minutes % 60

    return f"{int(hours):02}:{int(minutes):02}"


def get_time():
    return datetime.datetime.now()
