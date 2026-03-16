import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

DATA_FILE = "data.json"

# ── Constants ──────────────────────────────────────────────────────────────────
PRIORITY_ICON  = {"high": "🔴", "medium": "🟡", "low": "🟢"}
PRIORITY_LABEL = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
SPECIES_EMOJI  = {"dog": "🐕", "cat": "🐈", "rabbit": "🐇", "bird": "🐦", "other": "🐾"}
FREQ_LABEL     = {"daily": "🔁 Daily", "weekly": "📅 Weekly", "as_needed": "📌 As needed"}

TASK_EMOJI_KEYWORDS = {
    "walk":    "🦮", "run":    "🏃", "exercise": "🏃",
    "feed":    "🍽️", "food":   "🍽️", "meal":     "🍽️", "kibble":  "🍽️",
    "groom":   "✂️", "brush":  "✂️", "bath":     "🛁",
    "med":     "💊", "pill":   "💊", "medicine": "💊", "vet":     "🏥",
    "play":    "🎾", "toy":    "🎾", "enrich":   "🧩",
    "train":   "🎓", "nails":  "💅", "teeth":    "🦷",
    "water":   "💧", "litter": "🗑️",
}

def task_emoji(title: str) -> str:
    """Returns an emoji matching the task title keywords, or 📋 as default."""
    lower = title.lower()
    for kw, emoji in TASK_EMOJI_KEYWORDS.items():
        if kw in lower:
            return emoji
    return "📋"

# ── Session State ──────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = Owner.load_from_json(DATA_FILE)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Your daily pet care planner")
    st.divider()

    if st.session_state.owner:
        o = st.session_state.owner
        all_tasks   = o.get_all_tasks()
        done_count  = sum(1 for t in all_tasks if t.completed)
        total_count = len(all_tasks)
        pct = int(done_count / total_count * 100) if total_count else 0

        st.markdown(f"### 👤 {o.name}")
        st.markdown(f"⏱️ **{o.available_hours} hrs** available today")
        st.progress(pct, text=f"{done_count}/{total_count} tasks done ({pct}%)")
        st.divider()

        if o.pets:
            st.markdown("**Your pets**")
            for pet in o.pets:
                icon = SPECIES_EMOJI.get(pet.species, "🐾")
                pending = sum(1 for t in pet.tasks if not t.completed)
                st.markdown(f"{icon} **{pet.name}** — {pending} pending task(s)")
        st.divider()
        st.caption("Data auto-saved to `data.json`")
    else:
        st.info("Save your profile to get started.")

# ── Main layout ────────────────────────────────────────────────────────────────
st.markdown("## 🐾 PawPal+ &nbsp; <span style='font-size:1rem;color:gray'>Daily Pet Care Planner</span>",
            unsafe_allow_html=True)
st.divider()

# ── Section 1: Owner Profile ───────────────────────────────────────────────────
with st.expander("👤 Owner Profile", expanded=st.session_state.owner is None):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        owner_name = st.text_input("Your name",
                                   value=st.session_state.owner.name if st.session_state.owner else "Jordan")
    with col2:
        available_hours = st.number_input(
            "Hours available today", min_value=0.5, max_value=24.0,
            value=st.session_state.owner.available_hours if st.session_state.owner else 2.0,
            step=0.5)
    with col3:
        st.write("")
        st.write("")
        if st.button("💾 Save Profile"):
            if st.session_state.owner is None:
                st.session_state.owner = Owner(name=owner_name, available_hours=available_hours, ID="o1")
            else:
                st.session_state.owner.name = owner_name
                st.session_state.owner.set_availability(available_hours)
            st.session_state.owner.save_to_json(DATA_FILE)
            st.success(f"Profile saved for **{owner_name}**!")
            st.rerun()

if st.session_state.owner is None:
    st.stop()

owner: Owner = st.session_state.owner

# ── Section 2: Pets ────────────────────────────────────────────────────────────
with st.expander("🐾 Manage Pets", expanded=not owner.pets):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add Pet"):
            if pet_name in [p.name for p in owner.pets]:
                st.warning(f"**{pet_name}** is already in your list.")
            else:
                pet_id = f"p{len(owner.pets) + 1}"
                owner.add_pet(Pet(name=pet_name, species=species, ID=pet_id, owner_id=owner.ID))
                owner.save_to_json(DATA_FILE)
                st.success(f"Added {SPECIES_EMOJI.get(species,'🐾')} **{pet_name}** the {species}!")
                st.rerun()

    if owner.pets:
        st.write("**Current pets:**")
        pet_cols = st.columns(len(owner.pets))
        for col, pet in zip(pet_cols, owner.pets):
            icon = SPECIES_EMOJI.get(pet.species, "🐾")
            pending = sum(1 for t in pet.tasks if not t.completed)
            col.metric(f"{icon} {pet.name}", pet.species.title(), f"{pending} pending")

if not owner.pets:
    st.info("Add at least one pet above to continue.")
    st.stop()

st.divider()

# ── Section 3: Tasks ───────────────────────────────────────────────────────────
st.subheader("📋 Tasks")

left, right = st.columns([1, 2])

with left:
    with st.container(border=True):
        st.markdown("**Add a task**")
        pet_names = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("For pet", pet_names)
        selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

        task_title = st.text_input("Task title", value="Morning walk")
        col_a, col_b = st.columns(2)
        with col_a:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col_b:
            priority = st.selectbox("Priority", ["high", "medium", "low"])

        col_c, col_d = st.columns(2)
        with col_c:
            start_time = st.text_input("Start time (HH:MM)", value="", placeholder="08:00")
        with col_d:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"],
                                     format_func=lambda f: FREQ_LABEL.get(f, f))

        description = st.text_input("Notes", value="", placeholder="Optional")

        if st.button("➕ Add Task", use_container_width=True):
            selected_pet.add_task(Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                start_time=start_time.strip(),
                frequency=frequency,
                description=description,
            ))
            owner.save_to_json(DATA_FILE)
            st.success(f"{task_emoji(task_title)} **{task_title}** added to {selected_pet_name}.")
            st.rerun()

with right:
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        scheduler = Scheduler()
        PORDER = {"high": 0, "medium": 1, "low": 2}

        ctrl1, ctrl2 = st.columns(2)
        with ctrl1:
            filter_priority = st.selectbox(
                "Filter", ["All priorities", "🔴 High only", "🟡 Medium only", "🟢 Low only"])
        with ctrl2:
            sort_mode = st.radio("Sort", ["By start time", "By priority"], horizontal=True)

        display_tasks = (
            sorted(all_tasks, key=lambda t: (PORDER.get(t.priority, 3), t.start_time or "99:99"))
            if sort_mode == "By priority"
            else scheduler.sort_by_time(all_tasks)
        )
        if filter_priority != "All priorities":
            pk = filter_priority.split()[1].lower()
            display_tasks = [t for t in display_tasks if t.priority == pk]

        task_to_pet = {id(t): p.name for p in owner.pets for t in p.tasks}

        total_shown = len(display_tasks)
        done_shown  = sum(1 for t in display_tasks if t.completed)
        st.caption(f"Showing {total_shown} task(s) — {done_shown} done, {total_shown - done_shown} pending")

        for t in display_tasks:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([0.4, 2.8, 1.2, 1.2, 0.6])
                c1.markdown(f"## {task_emoji(t.title)}")
                c2.markdown(
                    f"**{t.title}**  \n"
                    f"{SPECIES_EMOJI.get(task_to_pet.get(id(t), ''), '🐾')} *{task_to_pet.get(id(t), '?')}*"
                )
                c3.markdown(
                    f"{PRIORITY_LABEL.get(t.priority, t.priority)}  \n"
                    f"{FREQ_LABEL.get(t.frequency, t.frequency)}"
                )
                c4.markdown(
                    f"🕐 {t.start_time if t.start_time else '--'}  \n"
                    f"⏱️ {t.duration_minutes} min  \n"
                    f"📅 due {t.due_date}"
                )
                c5.markdown(f"## {'✅' if t.completed else '⬜'}")
                if t.description:
                    st.caption(f"💬 {t.description}")
    else:
        st.info("No tasks yet — add one on the left.")

st.divider()

# ── Section 4: Mark Complete ───────────────────────────────────────────────────
pending_tasks = owner.get_pending_tasks()
if pending_tasks:
    with st.expander("✅ Mark a Task Complete", expanded=False):
        task_to_complete = st.selectbox(
            "Select task",
            options=pending_tasks,
            format_func=lambda t: f"{task_emoji(t.title)} {t.title} — {t.frequency}"
        )
        if st.button("✅ Mark as Done", use_container_width=False):
            for pet in owner.pets:
                if task_to_complete in pet.tasks:
                    pet.complete_task(task_to_complete.title)
                    owner.save_to_json(DATA_FILE)
                    if task_to_complete.frequency in ("daily", "weekly"):
                        st.success(
                            f"✅ **{task_to_complete.title}** done!  "
                            f"Next {task_to_complete.frequency} occurrence scheduled automatically.")
                    else:
                        st.success(f"✅ **{task_to_complete.title}** marked complete.")
                    st.rerun()
                    break

st.divider()

# ── Section 5: Schedule ────────────────────────────────────────────────────────
st.subheader("📅 Today's Schedule")

sched_col1, sched_col2 = st.columns([3, 1])
with sched_col2:
    weighted_mode = st.toggle(
        "⚖️ Weighted scoring",
        value=False,
        help="ON: uses urgency score (priority + overdue bonus + efficiency bonus)"
    )

with sched_col1:
    generate = st.button("🗓️ Generate Schedule", use_container_width=True)

if generate:
    schedule = owner.see_schedule(weighted=weighted_mode)
    scheduler = Scheduler()

    # ── Conflict warnings ──────────────────────────────────────────────────────
    if schedule.conflicts:
        st.error(f"⚠️ {len(schedule.conflicts)} conflict(s) detected — review before following this schedule.")
        for w in schedule.conflicts:
            if "overlaps" in w:
                st.warning(f"🕐 **Time overlap:** {w}")
            else:
                st.warning(f"📊 **Care cap exceeded:** {w}")

    if not schedule.tasks:
        st.warning("⚠️ No tasks fit within your available time, or all tasks are already completed.")
    else:
        total_min  = schedule.get_total_duration()
        remaining  = owner.available_hours * 60 - total_min
        used_pct   = int(total_min / (owner.available_hours * 60) * 100)

        # ── Summary metrics ────────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tasks scheduled",   len(schedule.tasks))
        m2.metric("Time used",         f"{total_min} min")
        m3.metric("Time remaining",    f"{remaining:.0f} min")
        m4.metric("Schedule fullness", f"{used_pct}%")

        mode_label = "⚖️ Weighted urgency" if weighted_mode else "🏷️ Priority + duration"
        st.caption(f"Ranking mode: **{mode_label}**")
        st.divider()

        # ── Task cards ─────────────────────────────────────────────────────────
        for i, task in enumerate(schedule.tasks, start=1):
            with st.container(border=True):
                h1, h2, h3, h4, h5 = st.columns([0.4, 3, 1.2, 1, 1])

                h1.markdown(f"## {task_emoji(task.title)}")
                h2.markdown(f"**{i}. {task.title}**")

                priority_badge = PRIORITY_LABEL.get(task.priority, task.priority)
                h3.markdown(priority_badge)
                h4.markdown(f"🕐 {task.start_time if task.start_time else '--'}  \n⏱️ {task.duration_minutes} min")

                if weighted_mode:
                    score = scheduler._score_task(task)
                    h5.metric("Score", f"{score:.0f}")

                # Reasoning caption
                reasons = []
                if task.priority == "high":
                    reasons.append("high priority")
                if task.start_time:
                    reasons.append(f"preferred at {task.start_time}")
                if task.description:
                    reasons.append(task.description)
                if weighted_mode:
                    from datetime import date
                    try:
                        days = (date.today() - date.fromisoformat(task.due_date)).days
                        if days > 0:
                            reasons.append(f"overdue by {days} day(s)")
                        elif days == 0:
                            reasons.append("due today")
                    except ValueError:
                        pass
                if reasons:
                    st.caption("💡 " + " · ".join(reasons))

        # ── Excluded tasks note ────────────────────────────────────────────────
        scheduled_ids = {id(t) for t in schedule.tasks}
        excluded = [t for t in owner.get_pending_tasks() if id(t) not in scheduled_ids]
        if excluded:
            with st.expander(f"⏭️ {len(excluded)} task(s) not scheduled (didn't fit in available time)"):
                for t in excluded:
                    st.markdown(
                        f"- {task_emoji(t.title)} **{t.title}** — "
                        f"{t.duration_minutes} min · {PRIORITY_LABEL.get(t.priority, t.priority)}"
                    )
