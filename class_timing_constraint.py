# This is the class timing constraint file- Shalaka

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
        self.lunch_start = LUNCH_BREAK_START
        self.lunch_end = LUNCH_BREAK_END
        self.break_one_start = BREAKONE_START_TIME
        self.break_one_end = BREAKONE_END_TIME
        self.break_two_start = BREAKTWO_START_TIME
        self.break_two_end = BREAKTWO_END_TIME

        # Now dynamically extract the break times
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
        # If the start_time and end_time are already datetime objects, directly format them.
        start_time_str = start_time.strftime("%H:%M")
        end_time_str = end_time.strftime("%H:%M")
        return (start_time_str, end_time_str)

    def is_timing_valid(self, time_slot):
        """
        Validates if a given time slot falls within valid university hours and excludes breaks.

        Args:
            time_slot (TimeSlot): The time slot to validate. It should have a start and end time in "HH:MM" format.

        Returns:
            bool: True if the time slot is valid (falls within university hours and doesn't overlap with breaks), False otherwise.
        """
        # Convert the start and end times from string format to datetime objects for comparison
        start = datetime.strptime(time_slot.start, "%H:%M")
        end = datetime.strptime(time_slot.end, "%H:%M")

        # Check if the time slot falls within university operating hours (e.g., 08:00 to 18:00)
        # If the class starts or ends outside university hours, return False
        if not (self.start_time <= start < self.end_time and self.start_time < end <= self.end_time):
            return False  # Time slot is outside university hours

        # Now, ensure that the time slot doesn't overlap with any break periods (lunch or other breaks)
        # Loop through each break time and check for overlaps
        for break_start, break_end in self.break_times:
            # Convert break times to datetime for comparison
            break_start_time = datetime.strptime(break_start, "%H:%M")
            break_end_time = datetime.strptime(break_end, "%H:%M")

            # Check if the time slot overlaps with any break (start or end within break period)
            if self.do_time_slots_intersect(start, end, break_start_time, break_end_time):
                return False  # Time slot overlaps with a break

        # If the time slot passed all checks, it is valid
        return True



    def _overlaps_with_break(self, start, end, break_start, break_end):
        """
        Helper method to check if a time slot overlaps with a break period.

        Args:
            start (datetime): Start time of the class.
            end (datetime): End time of the class.
            break_start (datetime): Start time of the break.
            break_end (datetime): End time of the break.

        Returns:
            bool: True if overlaps, False otherwise.
        """
        return max(start, break_start) < min(end, break_end)

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
        # No need to parse the datetime objects, they are already datetime objects
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
        conflicts = 0

        for scheduled_class in schedule.raw_schedule:
            if not self.is_timing_valid(scheduled_class.time_slot):
                conflicts += 1

        return conflicts
