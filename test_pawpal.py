from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Weighted scoring ───────────────────────────────────────────────────────────

def test_overdue_task_scores_higher_than_same_priority_current_task():
    """An overdue task should outscore a non-overdue task of equal priority."""
    scheduler = Scheduler()
    overdue = Task(title="Overdue Med", duration_minutes=10, priority="high",
                   due_date=(date.today() - timedelta(days=1)).isoformat())
    current = Task(title="Today Med",  duration_minutes=10, priority="high",
                   due_date=date.today().isoformat())
    assert scheduler._score_task(overdue) > scheduler._score_task(current)


def test_weighted_schedule_puts_overdue_task_first():
    """Weighted scheduling should place an overdue high-priority task before a
    same-priority task that is merely due today."""
    owner = Owner(name="Alex", available_hours=2.0, ID="o1")
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    pet.add_task(Task(title="Today Med",   duration_minutes=10, priority="high",
                      due_date=date.today().isoformat()))
    pet.add_task(Task(title="Overdue Med", duration_minutes=10, priority="high",
                      due_date=(date.today() - timedelta(days=2)).isoformat()))
    owner.add_pet(pet)

    schedule = owner.see_schedule(weighted=True)
    assert schedule.tasks[0].title == "Overdue Med"


# ── Existing tests ─────────────────────────────────────────────────────────────

def test_mark_complete_changes_task_status():
    """mark_complete() should flip completed from False to True."""
    task = Task(title="Morning Walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1


# ── Sorting ────────────────────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should return tasks ordered earliest start_time first."""
    tasks = [
        Task(title="Evening Walk", duration_minutes=25, priority="low",    start_time="17:00"),
        Task(title="Feeding",      duration_minutes=10, priority="high",   start_time="07:30"),
        Task(title="Grooming",     duration_minutes=20, priority="medium", start_time="10:00"),
    ]
    ordered = Scheduler().sort_by_time(tasks)
    assert [t.start_time for t in ordered] == ["07:30", "10:00", "17:00"]


def test_sort_by_time_puts_no_time_tasks_last():
    """Tasks without a start_time should sort to the end."""
    tasks = [
        Task(title="Playtime", duration_minutes=15, priority="low",  start_time=""),
        Task(title="Feeding",  duration_minutes=10, priority="high", start_time="08:00"),
    ]
    ordered = Scheduler().sort_by_time(tasks)
    assert ordered[0].title == "Feeding"
    assert ordered[1].title == "Playtime"


# ── Recurrence ─────────────────────────────────────────────────────────────────

def test_daily_task_creates_next_occurrence_on_complete():
    """Completing a daily task via complete_task() should add a new task due tomorrow."""
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    today = date.today().isoformat()
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high",
                      frequency="daily", due_date=today))

    pet.complete_task("Feeding")

    assert len(pet.tasks) == 2
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert pet.tasks[1].due_date == tomorrow
    assert pet.tasks[1].completed is False


def test_weekly_task_creates_occurrence_seven_days_later():
    """Completing a weekly task should schedule the next one 7 days out."""
    pet = Pet(name="Whiskers", species="Cat", ID="p2", owner_id="o1")
    today = date.today().isoformat()
    pet.add_task(Task(title="Grooming", duration_minutes=20, priority="medium",
                      frequency="weekly", due_date=today))

    pet.complete_task("Grooming")

    expected = (date.today() + timedelta(weeks=1)).isoformat()
    assert pet.tasks[1].due_date == expected


def test_as_needed_task_does_not_create_recurrence():
    """Completing an as_needed task should NOT add a follow-up task."""
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    pet.add_task(Task(title="Vet Visit", duration_minutes=60, priority="high",
                      frequency="as_needed"))

    pet.complete_task("Vet Visit")

    assert len(pet.tasks) == 1   # no new task added
    assert pet.tasks[0].completed is True


# ── Conflict detection ─────────────────────────────────────────────────────────

def test_overlapping_tasks_trigger_conflict_warning():
    """Two tasks whose time windows overlap should produce a conflict warning."""
    owner = Owner(name="Alex", available_hours=3.0, ID="o1")
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    # 08:00 + 30 min = 08:30 ; 08:15 starts inside that window
    pet.add_task(Task(title="Morning Walk", duration_minutes=30, priority="high", start_time="08:00"))
    pet.add_task(Task(title="Feeding",      duration_minutes=10, priority="high", start_time="08:15"))
    owner.add_pet(pet)

    schedule = owner.see_schedule()

    assert any("overlaps" in w for w in schedule.conflicts)


def test_exact_same_start_time_triggers_conflict():
    """Two tasks with identical start times should be flagged as conflicting."""
    owner = Owner(name="Alex", available_hours=3.0, ID="o1")
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    pet.add_task(Task(title="Task A", duration_minutes=20, priority="high", start_time="09:00"))
    pet.add_task(Task(title="Task B", duration_minutes=15, priority="high", start_time="09:00"))
    owner.add_pet(pet)

    schedule = owner.see_schedule()

    assert len(schedule.conflicts) >= 1


def test_non_overlapping_tasks_produce_no_time_conflict():
    """Tasks that don't overlap in time should produce zero conflict warnings."""
    owner = Owner(name="Alex", available_hours=3.0, ID="o1")
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    # 08:00 + 30 min = 08:30 ; 09:00 starts after that
    pet.add_task(Task(title="Morning Walk", duration_minutes=30, priority="high", start_time="08:00"))
    pet.add_task(Task(title="Feeding",      duration_minutes=10, priority="high", start_time="09:00"))
    owner.add_pet(pet)

    schedule = owner.see_schedule()

    assert schedule.conflicts == []


# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_pet_with_no_tasks_produces_empty_schedule():
    """An owner whose pet has no tasks should get an empty schedule."""
    owner = Owner(name="Alex", available_hours=2.0, ID="o1")
    owner.add_pet(Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1"))

    schedule = owner.see_schedule()

    assert schedule.tasks == []
    assert schedule.get_total_duration() == 0


def test_all_completed_tasks_produces_empty_schedule():
    """If every task is already done, the schedule should be empty."""
    owner = Owner(name="Alex", available_hours=2.0, ID="o1")
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    t = Task(title="Feeding", duration_minutes=10, priority="high")
    t.mark_complete()
    pet.add_task(t)
    owner.add_pet(pet)

    schedule = owner.see_schedule()

    assert schedule.tasks == []


def test_task_longer_than_available_time_is_excluded():
    """A task that exceeds available time should not appear in the schedule."""
    owner = Owner(name="Alex", available_hours=0.25, ID="o1")  # 15 min only
    pet = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
    pet.add_task(Task(title="Long Walk", duration_minutes=60, priority="high"))
    owner.add_pet(pet)

    schedule = owner.see_schedule()

    assert schedule.tasks == []
