# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    - It would have 5 classes: an Owner class, a Pet class, a Task class, a Schedule class, and a Scheduler class.
- What classes did you include, and what responsibilities did you assign to each?
    - Owner Class would have a name attribute and a number attribute that would specify how much time they have on their hands
    - Pet Class would have a name attribute and a species attribute
    - Task Class would have a title attribute, a number attribute that would tell the duration, and a priority attribute
    - Schedule Class would have a list of tasks and the total duration of the tasks
    - Scheduler Class would generate the day's itinerary for the user

**b. Design changes**

- Did your design change during implementation?
    - Yes, significantly. The initial design was a rough sketch; the final system is much richer.
- If yes, describe at least one change and why you made it.
    - **Tasks moved from Owner to Pet.** In the initial design, tasks were stored on the Owner. During implementation it became clear that tasks naturally belong to a specific pet — a walk belongs to the dog, not the owner. Moving tasks to Pet made the data model reflect reality and made methods like `get_all_tasks()` and filtering by pet much cleaner.
    - **Task gained five new attributes.** `start_time`, `due_date`, `frequency`, `completed`, and `description` were all added as the scheduler's capabilities grew. The initial design only had title, duration, and priority.
    - **Scheduler split into multiple private methods.** The original single `generate_schedule()` method grew unwieldy, so it was broken into `_sort_tasks()`, `_detect_time_conflicts()`, and `_detect_cap_conflicts()` — each with a single clear responsibility and its own test.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider?
    - **Available time** — the owner's `available_hours` is converted to minutes and used as a budget. Tasks are only added if they fit within the remaining budget.
    - **Task priority** — high-priority tasks are considered before medium and low. This ensures the most critical pet care (medications, feeding) is scheduled first.
    - **Task duration** — within the same priority level, shorter tasks are scheduled first. This is a deliberate "fit more in" strategy: a 10-minute feeding and a 20-minute grooming both rank as high priority, but the feeding is scheduled first so both can fit if time allows.
    - **Completion status** — already-completed tasks are excluded from the schedule entirely, including today's occurrence of a recurring task that was already done.
    - **Due date / recurrence** — daily and weekly tasks auto-generate a next occurrence when completed, using `timedelta` to advance the due date.

- How did you decide which constraints mattered most?
    - Available time and priority came first because they directly answer the user's core question: "What can I actually get done today, and in what order?" Duration as a tiebreaker was added after realizing that sorting by priority alone could leave short high-value tasks stuck behind long ones. Completion status was added to prevent re-scheduling tasks that were already done earlier in the day.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    - The scheduler uses a **greedy priority algorithm**: it sorts all pending tasks by priority (high → medium → low), then by shortest duration, and adds each one as long as it fits in the remaining time. Once a task is skipped because it doesn't fit, the scheduler keeps going and may fit a shorter lower-priority task instead. This means a 5-minute low-priority task could get scheduled while a 45-minute high-priority task gets dropped — which is not always what a pet owner would want.
    - The conflict detection checks for **overlapping time windows** (start_time + duration) but only warns — it does not remove or reorder the conflicting tasks. This means the schedule can still contain two tasks that overlap in time, and it is up to the user to resolve the conflict manually.

- Why is that tradeoff reasonable for this scenario?
    - For a daily pet care app, filling the available time as fully as possible is usually more useful than blocking the whole schedule on one big task that won't fit. The greedy approach is simple to understand, fast to run, and easy to explain to the user ("we fit the most important tasks that could be done today"). A more optimal algorithm (e.g., 0/1 knapsack) would find the globally best set of tasks but would be much harder to implement and explain. Since the number of pet care tasks per day is small (typically under 10), the greedy approach produces good-enough results with no meaningful performance cost.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project?
    - **Design brainstorming (Phase 1):** Used AI chat to convert a rough verbal description of classes and attributes into a formal Mermaid.js UML diagram. The AI asked clarifying questions (one-to-many pet relationships, priority data type, Schedule ownership) that I hadn't thought through yet — this forced early design decisions that saved refactoring later.
    - **Class stubs and method signatures (Phase 2):** Used AI to generate the initial dataclass skeletons and method stubs, then filled in the logic myself. Having stubs in place made it easier to reason about what each method needed to do before writing it.
    - **Algorithm implementation (Phase 3):** Used AI to suggest the overlap detection formula (`a_start < b_end AND b_start < a_end`) and `timedelta` usage for recurring tasks. In both cases I read the suggestion, understood it, and then typed it myself rather than accepting it blindly.
    - **Test generation (Phase 4):** Used AI to suggest edge cases I hadn't thought of (pet with no tasks, all tasks already completed, task duration exceeding available time). I reviewed each test for correctness before adding it to the suite.

- What kinds of prompts or questions were most helpful?
    - Specific, scoped questions worked best: "Based on my skeletons in `pawpal_system.py`, how should the Scheduler retrieve all tasks from the Owner's pets?" produced a clear, usable answer. Broad questions like "help me build a scheduler" produced generic responses that needed heavy editing. Asking "what are the most important edge cases to test for a pet scheduler with sorting and recurring tasks?" was especially productive for the test suite.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - When reviewing `_detect_time_conflicts`, the AI suggested replacing the `range(len(...))` loop with `itertools.combinations(timed, 2)`. The suggestion was technically correct and slightly shorter. I chose to keep the explicit loop because the index-based version makes the "compare every unique pair once" logic immediately visible without requiring the reader to know that `combinations(list, 2)` produces all unique pairs. For a project meant to demonstrate understanding, readability outweighed brevity.

- How did you evaluate or verify what the AI suggested?
    - For algorithm suggestions, I traced through a small example by hand before accepting them (e.g., verified the overlap formula with two tasks on paper). For structural suggestions (moving tasks from Owner to Pet), I asked "what breaks if I make this change?" and worked through the impact on other methods before committing. Every AI-suggested change was covered by a test before being considered done.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - **Core behavior:** task completion status change, pet task count after adding a task
    - **Sorting:** chronological order with mixed start times, tasks with no start time falling to the end
    - **Recurrence:** daily task creates a next-day occurrence, weekly task advances 7 days, as_needed task creates no follow-up
    - **Conflict detection:** partial time overlap triggers a warning, identical start times trigger a warning, non-overlapping tasks produce no false alarms
    - **Edge cases:** pet with no tasks, all tasks already completed, task longer than available time

- Why were these tests important?
    - Sorting and recurrence are the most complex behaviors in the system — bugs there would be silent (no crash, just wrong output). Testing them explicitly meant I could refactor the Scheduler's internals with confidence. The edge case tests were important because those are the situations most likely to cause unexpected crashes in a real demo — an empty pet list or a zero-task schedule should never break the UI.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - Confident for the cases covered: 13/13 tests pass, covering the full range of priority sorting, time sorting, recurrence for all three frequency types, both types of conflict detection, and five edge cases. I rate overall system confidence at 4/5.

- What edge cases would you test next if you had more time?
    - Recurring task whose next occurrence immediately creates a new conflict (daily task at 08:00 re-scheduled for tomorrow, but tomorrow already has a task at 08:00)
    - `edit_task()` and `edit_pet()` — these methods are untested; editing a task's `start_time` to create or resolve a conflict is not currently verified
    - Two pets with tasks at the same time — the current conflict detector checks across all tasks regardless of which pet owns them, which is correct, but this scenario has no dedicated test
    - Owner with zero available hours — `available_hours = 0` should produce an empty schedule without dividing by zero

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    - The conflict detection system. It started as a single `_detect_conflicts` method and grew into two cleanly separated methods (`_detect_time_conflicts` and `_detect_cap_conflicts`) each with their own tests and their own warning label in the UI. The fact that it warns without ever crashing or silently modifying the schedule feels like a genuine design decision, not just a coding task. Seeing "Time overlap: 'Feeding' (08:15, 10 min) overlaps 'Morning Walk' (08:00, 30 min)" print correctly in the terminal was a clear moment where the system was doing something genuinely useful.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - **Persistent storage.** Right now all data lives in `st.session_state` and disappears when the browser tab closes. Adding JSON serialization (or a lightweight SQLite database) would make the app usable day-to-day, not just as a demo.
    - **Smarter recurrence handling.** The current system creates a new Task object when a recurring task is completed, but the old completed task stays in the list permanently. Over time this causes the task list to grow. A cleanup pass that removes completed non-recurring tasks and archives completed occurrences would keep the data tidy.
    - **UI for editing tasks.** The `edit_task()` method exists in the backend but there is no form for it in the Streamlit UI. A user who makes a typo in a task title currently has no way to fix it without restarting the session.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    - The most valuable thing AI did in this project was ask questions, not write code. When I described my initial design in plain English, the AI's clarifying questions — "can an owner have multiple pets?", "what values does priority hold?", "is a Schedule tied to a Pet or an Owner?" — forced me to make design decisions I had been vague about. Those decisions shaped every class and method that followed. The lesson is that AI is most useful as a thinking partner during design, not as a code generator during implementation. When I used it to generate code directly (early sessions), I got working code I didn't fully understand. When I used it to stress-test my design first, I wrote better code myself.
