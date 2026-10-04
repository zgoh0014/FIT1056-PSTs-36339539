# gui/roster_pages.py - The Daily Roster & Check-in page (Fragment 4.3).
#
# Three sections for the front desk:
#   1. Daily Roster       - a timetable of every lesson on the chosen day.
#   2. Student Check-in   - record that a student has arrived for a course.
#   3. Today's Check-ins  - a live log, so the receptionist can confirm it worked.
#
# As with every gui/ file, this page only displays data and collects input.
# The roster search and the check-in itself are done by the ScheduleManager.

import datetime

import pandas as pd
import streamlit as st

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def show_roster_page(manager):
    """Renders the daily roster and check-in functionality."""
    st.header("Daily Roster")

    _show_roster_section(manager)
    st.divider()
    _show_check_in_section(manager)
    st.divider()
    _show_todays_check_ins(manager)


# ----------------------------------------------------------------------
# 1. View Roster
# ----------------------------------------------------------------------

def _show_roster_section(manager):
    """Day picker plus a table of that day's lessons, sorted by start time."""
    # Open on today's weekday, so the receptionist sees today's classes first.
    # weekday() is 0 for Monday ... 6 for Sunday, which lines up with DAYS.
    today_index = datetime.date.today().weekday()
    day = st.selectbox("Select a day", DAYS, index=today_index)

    # The manager returns (course, lesson) pairs already sorted by time.
    lessons = manager.get_lessons_for_day(day)

    if not lessons:
        st.info(f"No lessons scheduled for {day}.")
        return

    rows = []
    for course, lesson in lessons:
        teacher = manager.find_teacher_by_id(course.teacher_id)
        rows.append({
            "Time": lesson.get("start_time", "--:--"),
            "Course": course.name,
            "Instrument": course.instrument,
            "Teacher": teacher.name if teacher else "UNASSIGNED",
            "Room": lesson.get("room", "-"),
            "Students Enrolled": len(course.enrolled_student_ids),
        })

    col1, col2 = st.columns(2)
    col1.metric(f"Lessons on {day}", len(rows))
    col2.metric("Students expected", sum(r["Students Enrolled"] for r in rows))
    st.dataframe(pd.DataFrame(rows), hide_index=True)


# ----------------------------------------------------------------------
# 2. Student Check-in
# ----------------------------------------------------------------------

def _show_check_in_section(manager):
    """Pick a student, pick one of their courses, press Check-in."""
    st.subheader("Student Check-in")

    if not manager.students or not manager.courses:
        st.info("Add at least one student and one course before checking anyone in.")
        return

    # Dropdowns show readable names, but we keep the IDs behind them because
    # the manager works with IDs. A name->id dictionary would break if two
    # students shared a name, so we pass the objects and format them instead.
    student = st.selectbox(
        "Select Student",
        manager.students,
        format_func=lambda s: f"{s.name} (ID {s.id})",
    )

    # The course list depends on the student chosen above. Widgets inside an
    # st.form do not refresh until Submit, so the template's form could not do
    # this - these widgets sit outside a form, so the course list updates the
    # moment a different student is picked.
    enrolled = manager.get_courses_for_student(student.id)
    show_all = st.checkbox(
        "Include courses this student is not enrolled in (trial / drop-in lesson)",
        value=not enrolled,  # a student with no courses can only use "all"
    )
    course_options = manager.courses if show_all else enrolled

    if not course_options:
        st.info(f"{student.name} is not enrolled in any course yet.")
        return

    course = st.selectbox(
        "Select Course",
        course_options,
        format_func=lambda c: f"{c.name} (ID {c.id})",
    )

    if st.button("Check-in Student", type="primary"):
        is_enrolled = course.id in student.enrolled_course_ids
        success = manager.check_in(student.id, course.id)

        if success:
            st.success(f"Checked in {student.name} for {course.name}!")
            if not is_enrolled:
                # The manager allows this (a visitor sitting in) but the
                # receptionist should know it happened.
                st.warning(
                    f"Note: {student.name} is not enrolled in {course.name}. "
                    f"This was recorded as a drop-in."
                )
        else:
            st.error("Check-in failed. The student or course could not be found.")


# ----------------------------------------------------------------------
# 3. Today's check-ins
# ----------------------------------------------------------------------

def _show_todays_check_ins(manager):
    """Lists every check-in recorded today, newest first."""
    st.subheader("Today's Check-ins")
    # Drawn AFTER the check-in section on purpose: Streamlit runs top to
    # bottom, so a check-in made above already appears in this table.
    today = datetime.date.today().isoformat()
    records = manager.get_attendance_for_date(today)

    if not records:
        st.caption("No check-ins recorded yet today.")
        return

    rows = []
    for record in records:
        student = manager.find_student_by_id(record["student_id"])
        course = manager.find_course_by_id(record["course_id"])
        rows.append({
            "Time": record["timestamp"][11:19],  # "HH:MM:SS" part of the ISO string
            # A record can outlive the student/course it points to (e.g. after
            # a removal), so fall back to the raw ID instead of crashing.
            "Student": student.name if student else f"Student #{record['student_id']} (removed)",
            "Course": course.name if course else f"Course #{record['course_id']} (removed)",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True)
