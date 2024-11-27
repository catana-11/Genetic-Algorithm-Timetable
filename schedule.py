from dataclasses import dataclass, field
from datetime import datetime
from random import choice
from typing import List, Optional, Set
from class_timing_constraint import ClassTimingConstraint

from constants import (
    DAYS_OF_WEEK,
    LAB_TIME_SLOT_DURATION,
    LUNCH_BREAK_END,
    LUNCH_BREAK_START,
    TIME_SLOT_DURATION,
    UNIVERSITY_END_TIME,
    UNIVERSITY_START_TIME,
)
from models import (
    Course,
    Department,
    Division,
    Professor,
    Room,
    ScheduledClass,
    TimeSlot,
)


@dataclass(repr=True)
class ScheduleOptimizer:
    raw_schedule: List[ScheduledClass] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    lab_rooms: List[Room] = field(default_factory=list)
    time_slots: Set[TimeSlot] = field(default_factory=set)
    departments: List[Department] = field(default_factory=list)
    divisions: Set[Division] = field(default_factory=set)
    fitness: float = -1.0

    def register_room(self, new_room: Room) -> None:
        self.rooms.append(new_room)

    def register_lab_room(self, new_room: Room) -> None:
        self.lab_rooms.append(new_room)

    def register_time_slot(self, new_time_slot: TimeSlot) -> None:
        self.time_slots.add(new_time_slot)

    def register_department(self, new_dept: Department) -> None:
        self.departments.append(new_dept)

    def register_division(self, new_division: Division) -> None:
        self.divisions.add(new_division)

    def populate_time_slots(self) -> None:
        time_slot_id: int = 1

        for day in DAYS_OF_WEEK:
            current_time: datetime = UNIVERSITY_START_TIME
            while current_time + TIME_SLOT_DURATION <= UNIVERSITY_END_TIME:
                if LUNCH_BREAK_START <= current_time < LUNCH_BREAK_END:
                    current_time += TIME_SLOT_DURATION
                    continue

                self.register_time_slot(
                    TimeSlot(
                        slot_id=f"MT{time_slot_id}",
                        day=day,
                        start=current_time.strftime("%H:%M"),
                        end=(current_time + TIME_SLOT_DURATION).strftime("%H:%M"),
                        duration=TIME_SLOT_DURATION,
                    )
                )
                time_slot_id += 1

                if current_time + LAB_TIME_SLOT_DURATION <= UNIVERSITY_END_TIME:
                    self.register_time_slot(
                        TimeSlot(
                            slot_id=f"MT{time_slot_id}",
                            day=day,
                            start=current_time.strftime("%H:%M"),
                            end=(current_time + LAB_TIME_SLOT_DURATION).strftime("%H:%M"),
                            duration=LAB_TIME_SLOT_DURATION,
                        )
                    )
                    time_slot_id += 1

                current_time += TIME_SLOT_DURATION

    def create_schedule(self) -> "ScheduleOptimizer":
        self.raw_schedule.clear()
        divisions: Set[Division] = {Division("A", 2), Division("B", 2)}

        for department in self.departments:
            self._schedule_department(department, divisions)

        return self

    def _schedule_department(self, department: Department, divisions: Set[Division]) -> None:
        for course in department.offered_courses:
            for div in divisions:
                self._schedule_course_lectures(course, div, department)
                if course.weekly_labs > 0:
                    self._schedule_course_labs(course, div, department)

    def _schedule_course_lectures(self, course: Course, division: Division, dept: Department) -> None:
        lecture_slots: List[TimeSlot] = [
            slot for slot in self.time_slots if slot.duration == TIME_SLOT_DURATION
        ]
        if not lecture_slots:
            raise ValueError(f"Not enough free time slots for scheduling this lecture!")

        # Track attempts
        attempts = 0
        max_attempts = 20  # Set a maximum number of attempts to avoid infinite retry loop

        for _ in range(course.weekly_lectures):
            attempts += 1
            if attempts > max_attempts:
                print(f"Max attempts reached for scheduling {course.name}, skipping.")
                return

            random_lecture_slot: Optional[TimeSlot] = self._choose_random_time_slot(lecture_slots)
            if not random_lecture_slot:
                print(f"Skipping lecture {course.name} due to no available time slots!")
                continue

            # Check if the assigned professor of the course is available for this slot.
            for _ in range(10):
                if (
                    course.assigned_professor is not None
                    and random_lecture_slot is not None
                    and not course.assigned_professor.is_reserved(random_lecture_slot)
                ):
                    break
                random_lecture_slot = self._choose_random_time_slot(lecture_slots)
            else:
                continue

            if random_lecture_slot is None:
                continue

            lecture_slots.remove(random_lecture_slot)
            random_room: Optional[Room] = self._choose_available_room(random_lecture_slot)

            if random_room is None:
                print(f"Skipping lecture {course.name} due to no available rooms for {random_lecture_slot}")
                continue

            self.book_and_add_class(
                div=division,
                department=dept,
                course=course,
                time_slot=random_lecture_slot,
                room=random_room,
            )

    
    def _schedule_course_labs(self, course: Course, div: Division, dept: Department) -> None:
        lab_slots: List[TimeSlot] = [
            slot for slot in self.time_slots if slot.duration == LAB_TIME_SLOT_DURATION
        ]
        if not lab_slots:
            raise ValueError(f"Not enough free time slots to schedule this lab!")

        # Track attempts
        attempts = 0
        max_attempts = 20  # Set a maximum number of attempts to avoid infinite retry loop

        for _ in range(course.weekly_labs):
            for batch in range(1, div.num_batches + 1):
                attempts += 1
                if attempts > max_attempts:
                    print(f"Max attempts reached for scheduling {course.name} labs, skipping.")
                    return

                random_lab_slot: Optional[TimeSlot] = self._choose_random_time_slot(lab_slots)
                if not random_lab_slot:
                    print(f"Skipping lab {course.name} due to no available time slots!")
                    continue

                for _ in range(20):
                    if (
                        course.lab_professor is not None
                        and random_lab_slot is not None
                        and not course.lab_professor.is_reserved(random_lab_slot)
                    ):
                        break
                    random_lab_slot = self._choose_random_time_slot(lab_slots)
                else:
                    continue

                if random_lab_slot is None:
                    continue

                lab_slots.remove(random_lab_slot)
                random_room: Optional[Room] = self._choose_available_room(random_lab_slot)

                if random_room is None:
                    print(f"Skipping lab {course.name} due to no available rooms for {random_lab_slot}")
                    continue

                self.book_and_add_class(
                    div=div,
                    batch=str(batch),
                    department=dept,
                    time_slot=random_lab_slot,
                    course=course,
                    room=random_room,
                )




    def _choose_random_time_slot(time_slots: List[TimeSlot]) -> Optional[TimeSlot]:
        if not time_slots:
            print("No available time slots left!")
            return None
        return choice(time_slots)

    def _choose_available_room(self, time_slot: TimeSlot) -> Optional[Room]:
        available_rooms: List[Room] = [
            room for room in self.rooms if not room.is_reserved(time_slot)
        ]
        if not available_rooms:
            print(f"No available rooms for time slot {time_slot}!")
            return None
        return choice(available_rooms)

    def book_and_add_class(
            self,
            div: Division,
            department: Department,
            course: Course,
            time_slot: TimeSlot,
            room: Room,
            batch: Optional[str] = None,
        ) -> None:
        # Book the room
        room.reserve_room(time_slot)

        # Check if the professor is available
        if batch is not None and course.lab_professor is not None:
            if course.lab_professor.is_reserved(time_slot):
                print(f"Lab professor is already reserved for {time_slot}. Skipping.")
                return
            course.lab_professor.reserve_professor(time_slot)
            self.raw_schedule.append(
                ScheduledClass(
                    division=div,
                    batch="All" if not batch else f"Batch {batch}",
                    department=department,
                    course=course,
                    time_slot=time_slot,
                    room=room,
                    professor=course.lab_professor,
                )
            )
            return

        if course.assigned_professor is not None:
            if course.assigned_professor.is_reserved(time_slot):
                print(f"Professor is already reserved for {time_slot}. Skipping.")
                return
            course.assigned_professor.reserve_professor(time_slot)
            self.raw_schedule.append(
                ScheduledClass(
                    division=div,
                    batch="All" if not batch else f"Batch {batch}",
                    department=department,
                    course=course,
                    time_slot=time_slot,
                    room=room,
                    professor=course.assigned_professor,
                )
            )
            return

    def is_conflicting(self, time_slot: Optional[TimeSlot], room: Optional[Room], professor: Optional[Professor]) -> bool:
        if not time_slot or not room or not professor:
            return True

        for cls in self.raw_schedule:
            scheduled_time = cls.time_slot
            # Skip if the time slots are on different days
            if time_slot.day != scheduled_time.day:
                continue

            # Skip if the time slots do not overlap
            if (
                scheduled_time.end <= time_slot.start
                or time_slot.start >= scheduled_time.end
            ):
                continue

            # Conflict exists if the room or professor is already assigned.
            if cls.room == room or cls.professor == professor:
                return True

        return False


    def calculate_fitness(self) -> float:
        if len(self.raw_schedule) == 0:
            return 0.0

        conflicts = 0

        # Timing Constraint Check
        timing_constraint = ClassTimingConstraint()
        timing_conflicts = timing_constraint.check_timing_conflicts(self)
        conflicts += timing_conflicts
        print(f"Timing Conflicts: {timing_conflicts}")

        # Room and Professor Conflicts
        for i in range(len(self.raw_schedule)):
            for j in range(i + 1, len(self.raw_schedule)):
                if self.raw_schedule[i].conflicts_with(self.raw_schedule[j]):
                    conflicts += 1

        return 1 / (1 + conflicts)
