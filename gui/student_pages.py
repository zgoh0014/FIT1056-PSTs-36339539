# gui/student_pages.py - The Student Management page (Fragment 4.2).
#
# Two jobs for the receptionist:
#   1. Find a student  - search by name or ID and see their courses.
#   2. Register a new student - one form that creates the student AND enrols
#      them in a course for their chosen instrument.
#
# This file only draws widgets and shows results. Every search and every
# change is done by calling a ScheduleManager method.

import pandas as pd
import streamlit as st

# Key used to carry a success message across a st.rerun() (see below).
FLASH_KEY = "student_page_flash"


def show_student_management_page(manager):
    """Renders all components for the student management page."""
    st.header("Student Management")

    # A message saved just before the last st.rerun(). Showing it here, at the
    # top, means the receptionist sees it on the refreshed page.
    flash = st.session_state.pop(FLASH_KEY, None)
    if flash:
        st.success(flash)
        st.balloons()

    _show_search_section(manager)
    st.divider()
    _show_registration_section(manager)


# ----------------------------------------------------------------------
# Search
# ----------------------------------------------------------------------

def _show_search_section(manager):
    """Search box plus a results table. A blank search lists everyone."""
    st.subheader("Find a Student")
    query = st.text_input(
        "Search by name or student ID",
        placeholder="e.g. Alice, or 2",
        help="Partial names work and case does not matter. Leave blank to list every student.",
    )

    # The manager decides WHO matches; this page only decides how to show them.
    results = manager.search_students(query)

    if not results:
        st.info(f"No student matches '{query}'.")
        return

    st.dataframe(_students_to_table(manager, results), hide_index=True)
    if query.strip():
        st.caption(f"{len(results)} match(es) for '{query.strip()}'.")
    else:
        st.caption(f"{len(results)} student(s) on file.")


def _students_to_table(manager, students):
    """Turns StudentUser objects into a pandas DataFrame for st.dataframe."""
    rows = []
    for student in students:
        courses = manager.get_courses_for_student(student.id)
        rows.append({
            "ID": student.id,
            "Name": student.name,
            "Enrolled Courses": ", ".join(c.name for c in courses) if courses else "None",
            "Check-ins": len(manager.get_attendance_for_student(student.id)),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Registration
# ----------------------------------------------------------------------

def _show_registration_section(manager):
    """The Register New Student form."""
    st.subheader("Register New Student")

    # Show which instruments can be taught, so the receptionist knows what to
    # type. Built from the teachers on file, so it updates automatically when
    # a new teacher is added.
    instruments = sorted({t.speciality for t in manager.teachers if t.speciality})
    if instruments:
        st.caption("Instruments currently taught: " + ", ".join(instruments))

    # st.form groups the inputs so the page only re-runs when Submit is
    # pressed, not on every keystroke. clear_on_submit empties the boxes
    # ready for the next walk-in.
    with st.form("registration_form", clear_on_submit=True):
        reg_name = st.text_input("New Student Name")
        reg_instrument = st.text_input("First Instrument", placeholder="e.g. Piano")
        submitted = st.form_submit_button("Register Student", type="primary")

    if not submitted:
        return

    # Basic input checks belong in the View: they are about what was typed,
    # not about the school's rules.
    if not reg_name.strip() or not reg_instrument.strip():
        st.warning("Please enter both a name and an instrument.")
        return

    new_student = manager.register_new_student(reg_name, reg_instrument)

    if new_student:
        courses = manager.get_courses_for_student(new_student.id)
        course_name = courses[0].name if courses else "a course"
        # Save the message, then re-run so the search table above is redrawn
        # with the new student already in it.
        st.session_state[FLASH_KEY] = (
            f"Successfully registered {new_student.name} (Student ID {new_student.id}) "
            f"and enrolled them in {course_name}!"
        )
        st.rerun()
    else:
        st.error(
            f"Could not register {reg_name.strip()}. "
            f"No teacher for '{reg_instrument.strip()}' is available."
        )
