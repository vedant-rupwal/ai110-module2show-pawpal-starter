from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Any, Optional


@dataclass
class Task:
    """Represents a single pet care activity."""
    title: str
    duration_minutes: int
    priority: str
    description: str = ""
    frequency: str = "daily"        # "daily" | "weekly" | "as_needed"
    completed: bool = False
    start_time: str = ""            # optional preferred start time "HH:MM"
    due_date: str = field(default_factory=lambda: date.today().isoformat())

    def mark_complete(self) -> Optional['Task']:
        """Marks this task as completed.
        For daily/weekly tasks, returns a new Task instance due on the next occurrence.
        Returns None for as_needed tasks."""
        self.completed = True
        if self.frequency == "daily":
            next_due = date.fromisoformat(self.due_date) + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = date.fromisoformat(self.due_date) + timedelta(weeks=1)
        else:
            return None  # as_needed — no automatic next instance
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            description=self.description,
            frequency=self.frequency,
            start_time=self.start_time,
            due_date=next_due.isoformat(),
        )

    def reset(self) -> None:
        """Resets a recurring task so it can be scheduled again."""
        self.completed = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Task to a plain dictionary for JSON storage."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "description": self.description,
            "frequency": self.frequency,
            "completed": self.completed,
            "start_time": self.start_time,
            "due_date": self.due_date,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Task:
        """Reconstructs a Task from a plain dictionary."""
        return cls(
            title=d["title"],
            duration_minutes=d["duration_minutes"],
            priority=d["priority"],
            description=d.get("description", ""),
            frequency=d.get("frequency", "daily"),
            completed=d.get("completed", False),
            start_time=d.get("start_time", ""),
            due_date=d.get("due_date", date.today().isoformat()),
        )


@dataclass
class Pet:
    """Stores pet details and its associated tasks."""
    name: str
    species: str
    ID: str
    owner_id: str
    tasks: List[Task] = field(default_factory=list)
    max_care_minutes: Optional[int] = None  # daily cap for this pet (None = no cap)

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet's task list."""
        self.tasks.append(task)

    def edit_task(self, task_title: str, updates: Dict[str, Any]) -> None:
        """Updates attributes of an existing task by title and due_date-agnostic match."""
        for task in self.tasks:
            if task.title == task_title:
                for key, value in updates.items():
                    setattr(task, key, value)
                return

    def complete_task(self, task_title: str) -> None:
        """Marks a task complete; if recurring, adds the next occurrence automatically."""
        for task in self.tasks:
            if task.title == task_title and not task.completed:
                next_task = task.mark_complete()
                if next_task:
                    self.tasks.append(next_task)
                return

    def get_tasks_by_status(self, completed: bool) -> List[Task]:
        """Returns tasks filtered by completion status."""
        return [t for t in self.tasks if t.completed == completed]

    def reset_daily_tasks(self) -> None:
        """Resets all daily-frequency tasks so they can be rescheduled."""
        for task in self.tasks:
            if task.frequency == "daily":
                task.reset()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Pet and its tasks to a plain dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "ID": self.ID,
            "owner_id": self.owner_id,
            "max_care_minutes": self.max_care_minutes,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Pet:
        """Reconstructs a Pet (and its tasks) from a plain dictionary."""
        pet = cls(
            name=d["name"],
            species=d["species"],
            ID=d["ID"],
            owner_id=d["owner_id"],
            max_care_minutes=d.get("max_care_minutes"),
        )
        pet.tasks = [Task.from_dict(t) for t in d.get("tasks", [])]
        return pet


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""
    name: str
    available_hours: float
    ID: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a new pet to the owner's list."""
        self.pets.append(pet)

    def edit_pet(self, pet_name: str, updates: Dict[str, Any]) -> None:
        """Updates attributes of an existing pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                for key, value in updates.items():
                    setattr(pet, key, value)
                return

    def set_availability(self, hours: float) -> None:
        """Updates the owner's available hours."""
        self.available_hours = hours

    def get_all_tasks(self) -> List[Task]:
        """Returns all tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Returns all tasks belonging to a specific pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.tasks
        return []

    def get_pending_tasks(self) -> List[Task]:
        """Returns all incomplete tasks across all pets."""
        return [t for t in self.get_all_tasks() if not t.completed]

    def see_schedule(self, weighted: bool = False) -> 'Schedule':
        """Generates and returns the owner's daily schedule."""
        return Scheduler().generate_schedule(self, weighted=weighted)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Owner and all pets/tasks to a plain dictionary."""
        return {
            "name": self.name,
            "available_hours": self.available_hours,
            "ID": self.ID,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Owner:
        """Reconstructs an Owner (with pets and tasks) from a plain dictionary."""
        owner = cls(
            name=d["name"],
            available_hours=d["available_hours"],
            ID=d["ID"],
        )
        owner.pets = [Pet.from_dict(p) for p in d.get("pets", [])]
        return owner

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Persists the owner's full state (pets + tasks) to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> Optional[Owner]:
        """Loads and returns an Owner from a JSON file.
        Returns None if the file does not exist or cannot be parsed."""
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except (json.JSONDecodeError, KeyError):
            return None


@dataclass
class Schedule:
    """Represents the generated schedule for an owner."""
    owner: Owner
    tasks: List[Task] = field(default_factory=list)
    total_duration: int = 0
    conflicts: List[str] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Adds a task to the schedule."""
        self.tasks.append(task)
        self.total_duration += task.duration_minutes

    def get_total_duration(self) -> int:
        """Returns the total duration of all scheduled tasks in minutes."""
        return sum(task.duration_minutes for task in self.tasks)


class Scheduler:
    """Retrieves, organizes, and manages tasks across an owner's pets."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
    PRIORITY_WEIGHT = {"high": 30, "medium": 20, "low": 10}

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sorts tasks by start_time (HH:MM). Tasks with no time set sort to the end."""
        return sorted(tasks, key=lambda t: t.start_time if t.start_time else "99:99")

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sorts tasks by priority first, then by shortest duration (fits more in)."""
        return sorted(
            tasks,
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 3), t.duration_minutes)
        )

    def _score_task(self, task: Task) -> float:
        """Computes a weighted urgency score for a task.

        Score components:
          - Priority weight:  high=30, medium=20, low=10
          - Overdue bonus:    +20 if past due date
          - Due-today bonus:  +10 if due today
          - Efficiency bonus: up to +9 for short tasks (penalises tasks > 90 min)

        Higher score = scheduled first.
        """
        score = self.PRIORITY_WEIGHT.get(task.priority, 10)
        today = date.today()
        try:
            due = date.fromisoformat(task.due_date)
            days_overdue = (today - due).days
            if days_overdue > 0:
                score += 20          # overdue — must do today
            elif days_overdue == 0:
                score += 10          # due today
        except ValueError:
            pass                     # malformed date — no bonus, never raises
        score += max(0, 9 - task.duration_minutes // 10)  # shorter = slightly more efficient
        return score

    def _sort_tasks_weighted(self, tasks: List[Task]) -> List[Task]:
        """Sorts tasks by weighted urgency score (highest score first)."""
        return sorted(tasks, key=self._score_task, reverse=True)

    def _to_minutes(self, time_str: str) -> int:
        """Converts a 'HH:MM' string to total minutes since midnight."""
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)

    def _detect_time_conflicts(self, tasks: List[Task]) -> List[str]:
        """Checks all scheduled tasks for overlapping time windows.
        Only compares tasks that have a start_time set.
        Returns a list of warning strings — never raises."""
        warnings = []
        timed = [t for t in tasks if t.start_time]
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                a_start = self._to_minutes(a.start_time)
                b_start = self._to_minutes(b.start_time)
                a_end = a_start + a.duration_minutes
                b_end = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"Time conflict: '{a.title}' ({a.start_time}, {a.duration_minutes} min) "
                        f"overlaps '{b.title}' ({b.start_time}, {b.duration_minutes} min)."
                    )
        return warnings

    def _detect_cap_conflicts(self, owner: Owner) -> List[str]:
        """Returns warnings for any pet whose pending tasks exceed its daily care cap."""
        warnings = []
        for pet in owner.pets:
            if pet.max_care_minutes is None:
                continue
            pending_minutes = sum(t.duration_minutes for t in pet.tasks if not t.completed)
            if pending_minutes > pet.max_care_minutes:
                warnings.append(
                    f"{pet.name}: {pending_minutes} min of tasks exceeds "
                    f"the {pet.max_care_minutes} min daily care cap."
                )
        return warnings

    def generate_schedule(self, owner: Owner, weighted: bool = False) -> Schedule:
        """Generates a Schedule respecting available time and reporting conflicts.

        Args:
            owner:    The owner whose pets and tasks are used.
            weighted: If True, rank tasks by urgency score (priority + overdue bonus +
                      efficiency bonus) instead of the flat priority-then-duration sort.
        """
        pending = owner.get_pending_tasks()
        sorted_tasks = self._sort_tasks_weighted(pending) if weighted else self._sort_tasks(pending)

        all_conflicts = self._detect_cap_conflicts(owner) + self._detect_time_conflicts(sorted_tasks)
        schedule = Schedule(owner=owner, conflicts=all_conflicts)
        available_minutes = owner.available_hours * 60

        for task in sorted_tasks:
            if task.duration_minutes <= available_minutes:
                schedule.add_task(task)
                available_minutes -= task.duration_minutes

        return schedule
