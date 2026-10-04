# gui/main_dashboard.py - The main window and sidebar navigation (Fragment 4.1).
#
# launch() is called by main.py. It sets up the page, makes sure there is
# exactly ONE ScheduleManager for the whole session, draws the sidebar menu,
# and hands the manager to whichever page the receptionist picked.

import streamlit as st

from app.schedule import ScheduleManager
from gui.student_pages import show_student_management_page
from gui.roster_pages import show_roster_page

# The pages in the sidebar menu, in display order. Keeping them in one list
# means the radio button and the if/elif below can never get out of step.
PAGES = ["Student Management", "Daily Roster", "Payments (stub)"]


def launch():
    """Sets up the main Streamlit application window and navigation."""
    # Must be the first Streamlit call on every run of the script.
    st.set_page_config(
        layout="wide",
        page_title="Music School Management System",
        page_icon="🎵",
    )

    # Streamlit re-runs this whole script from the top every time the user
    # clicks anything. A plain "manager = ScheduleManager()" would therefore
    # re-create the manager (and re-read the JSON file) on every click.
    # st.session_state survives those re-runs, so we create the manager ONCE
    # and every later run reuses the same object - the same "one manager for
    # the whole program" rule main() followed in PST3.
    if "manager" not in st.session_state:
        st.session_state.manager = ScheduleManager()
    manager = st.session_state.manager

    # --- Sidebar ---------------------------------------------------------
    st.sidebar.title("🎵 MSMS Navigation")
    page = st.sidebar.radio("Go to", PAGES)

    # A small at-a-glance panel. It only READS from the manager.
    st.sidebar.divider()
    st.sidebar.caption("School at a glance")
    col1, col2, col3 = st.sidebar.columns(3)
    col1.metric("Students", len(manager.students))
    col2.metric("Teachers", len(manager.teachers))
    col3.metric("Courses", len(manager.courses))
    st.sidebar.caption("Every change is saved to data/msms.json immediately.")

    # --- Page routing ------------------------------------------------------
    # Each page is just a function that receives the shared manager. The
    # dashboard does not know or care what is on the page.
    if page == "Student Management":
        show_student_management_page(manager)
    elif page == "Daily Roster":
        show_roster_page(manager)
    elif page == "Payments (stub)":
        st.header("Payments")
        st.warning("This feature will be implemented in PST5.")
