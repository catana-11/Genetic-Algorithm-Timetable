# This is the class timing constraint file- Shalaka, Piyush

from datetime import datetime
from constants import (
    UNIVERSITY_START_TIME, UNIVERSITY_END_TIME,
    LUNCH_BREAK_START, LUNCH_BREAK_END,
    BREAKONE_START_TIME, BREAKONE_END_TIME,
    BREAKTWO_START_TIME, BREAKTWO_END_TIME
)

class ClassTimingConstraint:
    """
    Handles validation and constraints related to class timing.
    """

    def __init__(self):
        self.start_time = UNIVERSITY_START_TIME
        self.end_time = UNIVERSITY_END_TIME

        self.break_times = [
            self.extract_time(BREAKONE_START_TIME, BREAKONE_END_TIME),
            self.extract_time(LUNCH_BREAK_START, LUNCH_BREAK_END),
            self.extract_time(BREAKTWO_START_TIME, BREAKTWO_END_TIME)
        ]

    def extract_time(self, start_time, end_time):
        """
        Helper method to extract time in HH:MM format from datetime objects.
        
        Args:
            start_time (datetime): The start time as a datetime object.
            end_time (datetime): The end time as a datetime object.

        Returns:
            tuple: A tuple containing start and end times in 'HH:MM' format.
        """
        return start_time.strftime("%H:%M"), end_time.strftime("%H:%M")

    def is_timing_valid(self, time_slot):
        """
        Validates if a given time slot falls within valid university hours and excludes breaks.

        Args:
            time_slot (TimeSlot): The time slot to validate. It should have a start and end time in "HH:MM" format.

        Returns:
            bool: True if the time slot is valid (falls within university hours and doesn't overlap with breaks), False otherwise.
        """
        start = datetime.strptime(time_slot.start, "%H:%M")
        end = datetime.strptime(time_slot.end, "%H:%M")

        if not (self.start_time <= start < self.end_time and self.start_time < end <= self.end_time):
            return False

        if any(self.do_time_slots_intersect(start, end, datetime.strptime(break_start, "%H:%M"), datetime.strptime(break_end, "%H:%M")) for break_start, break_end in self.break_times):
            return False

        return True

    def do_time_slots_intersect(self, start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
        """
        Returns True if two time slots overlap.
        
        Args:
            start1 (datetime): Start time of the first time slot.
            end1 (datetime): End time of the first time slot.
            start2 (datetime): Start time of the second time slot.
            end2 (datetime): End time of the second time slot.

        Returns:
            bool: True if the time slots overlap, False otherwise.
        """
        return start1 < end2 and start2 < end1

    def get_break_times(self):
        """
        Returns the list of break times.
        """
        return self.break_times

    def check_timing_conflicts(self, schedule):
        """
        Checks for timing conflicts across a schedule.

        Args:
            schedule (ScheduleOptimizer): The schedule to validate.

        Returns:
            int: The number of timing conflicts.
        """
        return sum(1 for scheduled_class in schedule.raw_schedule if not self.is_timing_valid(scheduled_class.time_slot))

