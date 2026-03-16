# PawPal+ — Final UML Class Diagram

> Render this diagram using the VS Code "Markdown Preview Mermaid Support" extension,
> or paste it into https://mermaid.live to export as PNG.

```mermaid
classDiagram
    class Task {
        +String title
        +int duration_minutes
        +String priority
        +String description
        +String frequency
        +bool completed
        +String start_time
        +String due_date
        +mark_complete() Task
        +reset()
    }

    class Pet {
        +String name
        +String species
        +String ID
        +String owner_id
        +List~Task~ tasks
        +int max_care_minutes
        +add_task(task: Task)
        +edit_task(task_title: String, updates)
        +complete_task(task_title: String)
        +get_tasks_by_status(completed: bool) List~Task~
        +reset_daily_tasks()
    }

    class Owner {
        +String name
        +float available_hours
        +String ID
        +List~Pet~ pets
        +add_pet(pet: Pet)
        +edit_pet(pet_name: String, updates)
        +set_availability(hours: float)
        +get_all_tasks() List~Task~
        +get_tasks_for_pet(pet_name: String) List~Task~
        +get_pending_tasks() List~Task~
        +see_schedule() Schedule
    }

    class Schedule {
        +Owner owner
        +List~Task~ tasks
        +int total_duration
        +List~String~ conflicts
        +add_task(task: Task)
        +get_total_duration() int
    }

    class Scheduler {
        +PRIORITY_ORDER Dict
        +sort_by_time(tasks: List~Task~) List~Task~
        +generate_schedule(owner: Owner) Schedule
        -_sort_tasks(tasks: List~Task~) List~Task~
        -_to_minutes(time_str: String) int
        -_detect_time_conflicts(tasks: List~Task~) List~String~
        -_detect_cap_conflicts(owner: Owner) List~String~
    }

    Owner "1" --> "*" Pet : has
    Pet "1" --> "*" Task : owns
    Owner ..> Schedule : requests via see_schedule()
    Scheduler ..> Owner : reads pets and tasks
    Scheduler ..> Schedule : produces
    Schedule "*" --> "1" Owner : belongs to
    Schedule "*" --> "*" Task : contains
    Pet ..> Task : creates next occurrence via complete_task()
```

## Changes from initial design

| Change | Reason |
|---|---|
| Tasks moved from `Owner` to `Pet` | Tasks are naturally associated with a specific pet, not the owner globally |
| `Task` gained `start_time`, `due_date`, `frequency`, `completed` | Needed for time-based sorting, recurring logic, and conflict detection |
| `Pet` gained `complete_task()` and `max_care_minutes` | Handles recurrence auto-creation and per-pet care cap enforcement |
| `Owner` gained `get_all_tasks()`, `get_tasks_for_pet()`, `get_pending_tasks()` | Provides filtered views across all pets without the Scheduler needing direct pet access |
| `Schedule` gained `conflicts: List[str]` | Surfaces both time-overlap and care-cap warnings without crashing |
| `Scheduler` split conflict detection into `_detect_time_conflicts` and `_detect_cap_conflicts` | Separates two distinct types of warnings for clarity and testability |
| `Owner` and `Pet` gained `ID` / `owner_id` | Required for linking pets to owners and generating unique IDs in the UI |
