# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan and track daily care tasks for one or more pets. It uses a priority-based scheduling algorithm to build a realistic day plan within the owner's available time.

## Features

### Owner and pet management
- Register an owner profile with a name and daily available hours
- Add multiple pets, each with a name and species
- All data persists within the session using `st.session_state`

### Task management
- Add tasks to any pet with a title, duration, priority, optional start time, frequency, and notes
- Three priority levels: **high**, **medium**, **low**
- Three frequency modes: **daily**, **weekly**, **as_needed**

### Smart scheduling (`Scheduler` class)
- **Priority + duration sort** — tasks are ranked high → medium → low; ties are broken by shortest duration so more tasks fit into the available window
- **Time-based sort** — `sort_by_time()` orders the task list chronologically by `HH:MM` start time; tasks with no start time fall to the end
- **Available-time enforcement** — only tasks that fit within the owner's remaining minutes are added to the schedule; oversized tasks are skipped, not crashed on

### Recurring task auto-creation
- Marking a **daily** task complete automatically schedules the next occurrence for tomorrow (`due_date + 1 day` via `timedelta`)
- Marking a **weekly** task complete advances the due date by 7 days
- **As-needed** tasks are completed without generating a follow-up

### Weighted urgency scoring (Agent Mode feature)

The scheduler has two ranking modes selectable in the UI via a toggle:

| Mode | How tasks are ranked |
|---|---|
| **Standard** (default) | Priority tier (high → medium → low), ties broken by shortest duration |
| **Weighted** | Each task receives a numeric urgency score; highest score is scheduled first |

**Score formula (`Scheduler._score_task`):**

```
score = priority_weight          # high=30, medium=20, low=10
      + overdue_bonus            # +20 if past due_date
      + due_today_bonus          # +10 if due_date == today
      + efficiency_bonus         # max(0, 9 - duration_minutes // 10)
```

The efficiency bonus rewards shorter tasks slightly (a 5-minute task gets +9, a 90-minute task gets 0) without ever overriding priority. The overdue bonus ensures a medication task that was missed yesterday outranks a same-priority enrichment task due next week — even if they share the same priority label.

**How Agent Mode was used to implement this:**

Agent Mode was used to plan and execute the full change across multiple files in one pass:
1. Designed the score formula and asked: *"Given priority, due date, and duration, suggest a scoring function that keeps priority dominant but introduces urgency for overdue tasks without over-penalising long ones."* The agent proposed the additive formula above; the efficiency bonus cap at `duration // 10` was its suggestion to avoid negatively scoring long-duration high-priority tasks.
2. The agent identified every file that needed touching — `pawpal_system.py` (new methods), `Owner.see_schedule` (new parameter), `app.py` (toggle + score display), `tests/test_pawpal.py` (two new tests) — and applied all changes in sequence rather than requiring manual back-and-forth across files.
3. The final formula and test cases were verified by hand before accepting: traced through an overdue high-priority task (score = 30 + 20 + 8 = 58) vs. a same-priority current task (score = 30 + 10 + 8 = 48) to confirm the ordering was correct.

### Conflict detection (warnings, never crashes)
- **Time-overlap warning** — if any two scheduled tasks with start times have overlapping windows (`start < other_end AND other_start < end`), a warning is displayed above the schedule
- **Care cap warning** — if a pet's total pending task time exceeds its `max_care_minutes` limit, the owner is alerted

### Streamlit UI
- Task table sorted by start time on every re-render
- Conflict warnings displayed with labelled `st.warning` blocks before the schedule
- Priority badges with color indicators (🔴 high / 🟡 medium / 🟢 low)
- "Mark Complete" dropdown triggers recurrence logic directly from the browser

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

The `Scheduler` class goes beyond a simple sorted list. It applies four layers of logic when building a daily plan:

| Feature | How it works |
|---|---|
| **Priority + duration sort** | Tasks are sorted high → medium → low priority; ties broken by shortest duration first so more tasks fit in the available window |
| **Time-based sort** | `sort_by_time()` orders tasks by their `start_time` (HH:MM); tasks with no time set fall to the end |
| **Recurring tasks** | Marking a `daily` or `weekly` task complete automatically creates the next occurrence with a due date advanced by 1 day or 7 days (`timedelta`); `as_needed` tasks are not repeated |
| **Conflict detection** | Two types of warnings are returned — (1) a per-pet **care cap** warning if pending task minutes exceed `max_care_minutes`, and (2) a **time overlap** warning if any two timed tasks have overlapping windows. Warnings are surfaced to the user; the schedule is never silently modified |

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/ -v
```

### What the tests cover

| Category | Tests | Description |
|---|---|---|
| **Core behavior** | `test_mark_complete_changes_task_status` | Completing a task flips its status to `True` |
| | `test_add_task_increases_pet_task_count` | Adding a task to a Pet grows its task list |
| **Sorting** | `test_sort_by_time_returns_chronological_order` | Tasks added out of order come back sorted by `HH:MM` |
| | `test_sort_by_time_puts_no_time_tasks_last` | Tasks with no `start_time` fall to the end without crashing |
| **Recurring tasks** | `test_daily_task_creates_next_occurrence_on_complete` | Completing a daily task adds a new task due tomorrow |
| | `test_weekly_task_creates_occurrence_seven_days_later` | Weekly tasks advance the due date by 7 days |
| | `test_as_needed_task_does_not_create_recurrence` | `as_needed` tasks do not spawn a follow-up |
| **Conflict detection** | `test_overlapping_tasks_trigger_conflict_warning` | Partial time overlap produces a warning |
| | `test_exact_same_start_time_triggers_conflict` | Two tasks at the same start time are flagged |
| | `test_non_overlapping_tasks_produce_no_time_conflict` | Sequential tasks produce zero false alarms |
| **Edge cases** | `test_pet_with_no_tasks_produces_empty_schedule` | A pet with no tasks returns an empty schedule |
| | `test_all_completed_tasks_produces_empty_schedule` | All-done task lists produce nothing to schedule |
| | `test_task_longer_than_available_time_is_excluded` | Oversized tasks are skipped, not crashed on |

### Confidence level

★★★★☆ (4 / 5)

The core scheduling behaviors — priority sorting, recurrence, and conflict detection — are fully tested across happy paths and key edge cases, and all 13 tests pass. The one missing star reflects areas not yet covered by automated tests: the Streamlit UI layer, editing existing tasks or pets, and interaction between recurring tasks and the conflict detector when a next-occurrence task creates a new overlap.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
