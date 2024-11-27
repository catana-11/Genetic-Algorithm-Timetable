from random import choice, random, sample
from typing import Callable, List
from class_timing_constraint import ClassTimingConstraint

from models import ScheduledClass, TimeSlot
from schedule import ScheduleOptimizer


class Population:

    def __init__(
        self, size: int, schedule_factory: Callable[[], ScheduleOptimizer], timing_constraint: ClassTimingConstraint
    ) -> None:
        """
        Initialize the population of schedules with given constraints.

        Args:
            size (int): The number of schedules in the population.
            schedule_factory (Callable): A function that generates a new schedule.
            timing_constraint (ClassTimingConstraint): The timing constraint to ensure validity of each schedule.
        """
        if not size > 0:
            raise ValueError("Expected a valid positive integer for size.")

        self.size: int = size
        self.schedules: List[ScheduleOptimizer] = [
            self._create_independent_schedule(schedule_factory, timing_constraint) for _ in range(size)
        ]

    def _create_independent_schedule(
        self, schedule_factory: Callable[[], ScheduleOptimizer], timing_constraint: ClassTimingConstraint
    ) -> ScheduleOptimizer:
        """
        Create an independent schedule, ensuring it adheres to the timing constraints.

        Args:
            schedule_factory (Callable): A function that generates a new schedule.
            timing_constraint (ClassTimingConstraint): The timing constraint to ensure validity of the schedule.

        Returns:
            ScheduleOptimizer: A valid schedule.
        """
        max_retries = 100
        retries = 0
        # Generate a schedule from the factory function
        schedule = schedule_factory()

        while not self.is_valid_schedule(schedule, timing_constraint) and retries < max_retries:
            schedule = schedule_factory()  # Generate a new schedule if the current one doesn't meet constraints
            retries += 1
        
        if retries == max_retries:
            raise ValueError("Could not generate a valid schedule after maximum retries.")
        
        return schedule


    def is_valid_schedule(
        self, schedule: ScheduleOptimizer, timing_constraint: ClassTimingConstraint
    ) -> bool:
        """
        Check if the generated schedule complies with timing constraints, ensuring no break overlap.

        Args:
            schedule (ScheduleOptimizer): The schedule to check.
            timing_constraint (ClassTimingConstraint): The timing constraint to ensure validity.

        Returns:
            bool: True if the schedule is valid, False otherwise.
        """
        for scheduled_class in schedule.raw_schedule:  # Assuming schedule.raw_schedule is a list of classes
            if not timing_constraint.is_timing_valid(scheduled_class.time_slot):
                return False  # Invalid if any class's time overlaps with breaks or is out of bounds
        return True


    def evaluate_fitness(self) -> None:
        for schedule in self.schedules:
            schedule.fitness = schedule.calculate_fitness()

    def get_best_schedule(self) -> ScheduleOptimizer:
        return max(self.schedules, key=lambda s: s.fitness)

    def select_parents(self) -> List[ScheduleOptimizer]:
        total_fitness: float = sum(schedule.fitness for schedule in self.schedules)
        if total_fitness == 0:
            return sample(
                self.schedules, 2
            )  # If all fitnesses are 0, we will select randomly

        return [
            self._roulette_selection(total_fitness),
            self._roulette_selection(total_fitness),
        ]

    def _roulette_selection(self, total_fitness: float) -> ScheduleOptimizer:
        pick: float = random() * total_fitness
        current: float = 0
        for schedule in self.schedules:
            current += (
                schedule.fitness
                if schedule.fitness != 0
                else schedule.calculate_fitness()
            )
            if current > pick:
                return schedule

        # In case of rounding errors, return the last one
        return self.schedules[-1]


class EvolutionManager:
    """
    Handles the evolutionary process for optimizing schedules using genetic algorithms.

    Attributes:
        _mutation_rate (float): The probability of mutation occurring during evolution.
        _crossover_rate (float): The probability of crossover occurring during evolution.
    """

    def __init__(self, mutation_rate: float, crossover_rate: float) -> None:
        """
        Initializes the EvolutionManager with mutation and crossover rates.

        Args:
            mutation_rate (float): The probability of mutation (must be > 0.0).
            crossover_rate (float): The probability of crossover (must be > 0.0).

        Raises:
            ValueError: If either mutation_rate or crossover_rate is not a positive float.
        """
        if not isinstance(mutation_rate, float) or not mutation_rate > 0.0:
            raise ValueError(f"Expected a positive float mutation rate")

        if not isinstance(crossover_rate, float) or not crossover_rate > 0.0:
            raise ValueError(f"Expected a positive float crossover rate")

        self._mutation_rate: float = mutation_rate
        self._crossover_rate: float = crossover_rate

    def mutate(self, schedule_optimizer: ScheduleOptimizer) -> None:
        random_class: ScheduledClass = choice(schedule_optimizer.raw_schedule)
        random_time_slot: TimeSlot = choice(list(schedule_optimizer.time_slots))
        
        if random() < self._mutation_rate:
            # Timing validation
            timing_constraint = ClassTimingConstraint()
            if not timing_constraint.is_timing_valid(random_time_slot):
                return  # Skip mutation if timing is invalid

            # Ensure no conflicts after mutation
            if not schedule_optimizer.is_valid_schedule(schedule_optimizer, timing_constraint):
                return  # Skip mutation if it creates invalid schedule

            random_class.time_slot = random_time_slot



    def crossover(
        self,
        parent_a: ScheduleOptimizer,
        parent_b: ScheduleOptimizer,
        schedule_factory: Callable[[], ScheduleOptimizer],
        timing_constraint: ClassTimingConstraint
    ) -> ScheduleOptimizer:
        """
        Creates an offspring schedule by combining the schedules of two parent schedules.
        This version ensures that the class timings and constraints are considered.

        Args:
            parent_a (ScheduleOptimizer): The first parent schedule.
            parent_b (ScheduleOptimizer): The second parent schedule.
            schedule_factory (Callable[[], ScheduleOptimizer]): A factory function for creating a new ScheduleOptimizer instance.
            timing_constraint (ClassTimingConstraint): A constraint to ensure that the schedule complies with timing rules.

        Returns:
            ScheduleOptimizer: The offspring schedule created from the two parents.
        """
        if random() > self._crossover_rate:
            # No crossover, return one parent
            return choice([parent_a, parent_b])

        # Initialize the offspring with a new schedule
        offspring = schedule_factory()

        # Ensure that the offspring's raw_schedule complies with timing constraints
        offspring.raw_schedule = []
        for class_a, class_b in zip(parent_a.raw_schedule, parent_b.raw_schedule):
            # Check that both classes are valid before attempting to select
            if class_a is not None and class_b is not None:
                selected_class = choice([class_a, class_b])

                # Ensure the selected class's timing is valid according to the constraint
                while not timing_constraint.is_timing_valid(selected_class.time_slot):
                    selected_class = choice([class_a, class_b])  # If invalid, select again

                offspring.raw_schedule.append(selected_class)
            else:
                raise ValueError("Invalid class found in parent's schedule (None value).")

        # Copy other attributes from the parents, assuming no conflict
        offspring.rooms = parent_a.rooms.copy()
        offspring.lab_rooms = parent_a.lab_rooms.copy()
        offspring.time_slots = parent_a.time_slots.copy()
        offspring.departments = parent_a.departments.copy()
        offspring.divisions = parent_a.divisions.copy()

        # Calculate fitness for the new offspring
        offspring.fitness = offspring.calculate_fitness()

        return offspring



    def evolve(
        self, population: Population, schedule_factory: Callable[[], ScheduleOptimizer]
    ) -> Population:
        """
        Evolves a population to create the next generation of schedules.

        The evolution process involves selecting the best schedule, performing crossover
        and mutation, and forming a new population.

        Args:
            population (Population): The current population of schedules.
            schedule_factory (Callable[[], ScheduleOptimizer]): A factory function for creating a new ScheduleOptimizer instance.

        Returns:
            Population: The next generation of schedules.
        """
        next_generation: List[ScheduleOptimizer] = [population.get_best_schedule()]

        while len(next_generation) < len(population.schedules):
            parent_a, parent_b = population.select_parents()
            try:
                offspring = self.crossover(parent_a, parent_b, schedule_factory, timing_constraint=ClassTimingConstraint)
                self.mutate(offspring)
                next_generation.append(offspring)
            except Exception as e:
                print(f"Error during crossover/mutation: {e}")
                continue  # Skips this offspring if mutation or crossover fails

        # Include timing_constraint while creating a new population
        timing_constraint = ClassTimingConstraint()

        new_population: Population = Population(
            size=len(next_generation), schedule_factory=schedule_factory, timing_constraint=timing_constraint
        )
        new_population.schedules = next_generation
        new_population.evaluate_fitness()
        return new_population
