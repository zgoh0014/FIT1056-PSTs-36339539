# gui/main_dashboard.py - The main window and sidebar navigation (Fragment 4.1).
#
# launch() is called by main.py. It sets up the page, makes sure there is
# exactly ONE ScheduleManager for the whole session, draws the sidebar menu,
# and hands the manager to whichever page the receptionist picked.
#
# PST5: the Payments stub is replaced by the real Finance page, the sidebar
# gains a "Backup Now" button, and every page is wrapped in a safety net so an
# unexpected error shows a friendly message instead of crashing the app.

import os
import logging

import streamlit as st

from app.schedule import ScheduleManager
from app.admin_utils import backup_data, list_backups
from gui.student_pages import show_student_management_page
from gui.roster_pages import show_roster_page
from gui.finance_pages import show_finance_page

# The pages in the sidebar menu, in display order. Keeping them in one list
# means the radio button and the if/elif below can never get out of step.
PAGES = ["Student Management", "Daily Roster", "Payments"]


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

    _show_backup_panel(manager)

    # --- Page routing ------------------------------------------------------
    # Each page is just a function that receives the shared manager. The
    # dashboard does not know or care what is on the page.
    try:
        if page == "Student Management":
            show_student_management_page(manager)
        elif page == "Daily Roster":
            show_roster_page(manager)
        elif page == "Payments":
            show_finance_page(manager)
    except Exception:
        # Crash-proofing: anything we did not foresee is written to msms.log
        # with the full traceback (logging.exception), and the receptionist
        # sees a calm message instead of a red Streamlit stack trace.
        # st.rerun() works by raising a special exception, so it must be let
        # through untouched - otherwise every rerun would look like a crash.
        if _is_streamlit_control_flow():
            raise
        logging.exception(f"Unexpected error on the '{page}' page")
        st.error(
            "Something went wrong on this page. The details were written to msms.log. "
            "Your saved data is safe - please try again or switch pages."
        )


def _is_streamlit_control_flow():
    """True if the exception being handled is Streamlit's own rerun/stop signal."""
    import sys
    exc = sys.exc_info()[1]
    return type(exc).__name__ in ("RerunException", "StopException")


def _show_backup_panel(manager):
    """Sidebar 'Backup Now' button (optional part of Fragment 5.4)."""
    st.sidebar.divider()
    st.sidebar.caption("Data safety")
    if st.sidebar.button("Backup Now", use_container_width=True):
        path = backup_data(manager.data_path)
        if path:
            st.sidebar.success(f"Backup saved: {os.path.basename(path)}")
        else:
            st.sidebar.error("Backup failed - see msms.log for details.")
    backups = list_backups()
    if backups:
        st.sidebar.caption(f"{len(backups)} backup(s) on file. Latest: {os.path.basename(backups[0])}")
