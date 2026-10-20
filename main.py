# main.py - Application launcher.
#
# Since PST4 this file's job is to start the Streamlit GUI. All interface code
# lives in the gui/ package and all business logic stays in app/schedule.py.
#
# PST5 (Fragment 5.4): before the GUI is drawn we also
#   1. switch on logging (msms.log), and
#   2. take a timestamped backup of data/msms.json,
# so every session starts with a safe copy of the data and a record of events.
#
# Run it with:   streamlit run main.py
# (python main.py also works - see the fallback at the bottom.)

from gui.main_dashboard import launch
from app.admin_utils import init_logger, backup_data


def start_session():
    """Logging + backup, done ONCE per browser session.

    Streamlit re-runs this whole file on every click. Without the
    session_state check, every click would create another backup file.
    """
    import logging
    import streamlit as st

    # Logging first, so the backup (and everything after it) is logged.
    # init_logger is safe to call on every re-run - it never adds a second
    # handler for the same file.
    init_logger()

    if "session_started" not in st.session_state:
        st.session_state.session_started = True
        logging.info("New MSMS session started.")
        backup_data()


if __name__ == "__main__":
    # "streamlit run main.py" executes this file inside a Streamlit server, so
    # runtime.exists() is True and we set up the session and draw the GUI.
    from streamlit import runtime

    if runtime.exists():
        start_session()
        launch()
    else:
        # Someone typed "python main.py" (the PST1-3 habit). Instead of showing a
        # wall of Streamlit warnings, start the Streamlit server on this same file
        # for them - exactly as if they had typed "streamlit run main.py".
        import sys
        from streamlit.web import cli as stcli

        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
