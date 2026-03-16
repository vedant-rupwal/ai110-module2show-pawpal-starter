from pawpal_system import Owner, Pet, Task

owner = Owner(name="Alex", available_hours=3.0, ID="o1")

dog = Pet(name="Buddy", species="Dog", ID="p1", owner_id="o1")
cat = Pet(name="Whiskers", species="Cat", ID="p2", owner_id="o1")

# Intentional overlap: Morning Walk starts 08:00 (30 min) -> ends 08:30
#                      Feeding starts 08:15 (10 min)      -> ends 08:25  [OVERLAP]
dog.add_task(Task(title="Morning Walk", duration_minutes=30, priority="high",   start_time="08:00", frequency="daily"))
dog.add_task(Task(title="Feeding",      duration_minutes=10, priority="high",   start_time="08:15", frequency="daily", description="Dry kibble"))

# No conflict: Grooming starts 10:00 (20 min) -> ends 10:20
#              Playtime starts 11:00 (15 min)  -> ends 11:15  [no overlap]
cat.add_task(Task(title="Grooming",     duration_minutes=20, priority="medium", start_time="10:00", frequency="weekly"))
cat.add_task(Task(title="Playtime",     duration_minutes=15, priority="low",    start_time="11:00", frequency="as_needed"))

owner.add_pet(dog)
owner.add_pet(cat)

schedule = owner.see_schedule()

print("-- Conflict Warnings --")
if schedule.conflicts:
    for w in schedule.conflicts:
        print(f"  !! {w}")
else:
    print("  No conflicts.")

print("\n" + "=" * 44)
print("           TODAY'S SCHEDULE")
print(f"  Owner: {owner.name}  |  Available: {owner.available_hours} hrs")
print("=" * 44)
for i, task in enumerate(schedule.tasks, start=1):
    time_label = f"@{task.start_time}" if task.start_time else ""
    print(f"{i}. [{task.priority.upper()}] {task.title} {time_label} ({task.duration_minutes} min)")
print("-" * 44)
remaining = owner.available_hours * 60 - schedule.get_total_duration()
print(f"Total: {schedule.get_total_duration()} min  |  Remaining: {remaining:.0f} min")
print("=" * 44)
