# main.py - GUI Launcher (Fragment 4.1).
#
# Since PST4 this file's ONLY job is to start the Streamlit GUI. All interface
# code lives in the gui/ package and all business logic stays in
# app/schedule.py, so nothing here needs to change when a page is added.
#
# Run it with:   streamlit run main.py
# (python main.py also works - see the fallback at the bottom.)

from gui.main_dashboard import launch

if __name__ == "__main__":
    # "streamlit run main.py" executes this file inside a Streamlit server, so
    # runtime.exists() is True and we simply draw the GUI.
    from streamlit import runtime

    if runtime.exists():
        launch()
    else:
        # Someone typed "python main.py" (the PST1-3 habit). Instead of showing a
        # wall of Streamlit warnings, start the Streamlit server on this same file
        # for them - exactly as if they had typed "streamlit run main.py".
        import sys
        from streamlit.web import cli as stcli

        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
