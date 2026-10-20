# app/admin_utils.py - Administrative tools: logging and backups (Fragment 5.3).
#
# These are "behind the scenes" tools for whoever runs the school's computer:
#   - init_logger()  writes every important event (registrations, payments,
#                    cancellations, errors) to msms.log, so problems can be
#                    traced after the fact.
#   - backup_data()  copies data/msms.json to data/backups/ with a timestamp in
#                    the file name, so a bad change can always be undone.
#
# They live outside ScheduleManager because they are not school business rules
# - they are about looking after the program itself.

import os
import glob
import shutil
import logging
import datetime

# Paths are worked out relative to the project folder (one level above app/),
# the same way app/schedule.py finds data/msms.json, so the program behaves the
# same whichever folder the terminal is in.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG_FILE = os.path.join(BASE_DIR, "msms.log")
DEFAULT_DATA_PATH = os.path.join(BASE_DIR, "data", "msms.json")
DEFAULT_BACKUP_DIR = os.path.join(BASE_DIR, "data", "backups")

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def init_logger(log_file=DEFAULT_LOG_FILE, level=logging.INFO):
    """Configures the root logger to append to a log file.

    Safe to call more than once: Streamlit re-runs main.py on every click, and
    a plain logging.basicConfig() + a new handler each time would write every
    log line 2, 3, 4... times. So we only add a file handler if one for this
    exact file is not already attached.
    """
    root = logging.getLogger()
    root.setLevel(level)

    log_file = os.path.abspath(log_file)
    for handler in root.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file:
            return log_file  # already set up - nothing to do

    folder = os.path.dirname(log_file)
    if folder:
        os.makedirs(folder, exist_ok=True)
    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")  # "a" = append
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)

    print(f"Logging configured. Outputting to {log_file}")
    logging.info("Logger initialised.")
    return log_file


def backup_data(data_path=DEFAULT_DATA_PATH, backup_dir=DEFAULT_BACKUP_DIR, keep=20):
    """Creates a timestamped backup of the main data file.

    Returns the path of the new backup, or None if no backup could be made
    (e.g. the data file does not exist yet). It never raises, so a failed
    backup can never stop the application from starting.

    'keep' limits how many backups are kept - otherwise a new file every
    session would slowly fill the disk. The oldest ones are removed first.
    """
    if not os.path.exists(data_path):
        logging.warning(f"Backup skipped: {data_path} does not exist yet.")
        return None

    try:
        # Create the backup folder the first time.
        os.makedirs(backup_dir, exist_ok=True)

        # e.g. msms_backup_2026-10-20_15-42-07.json - this format sorts
        # alphabetically in date order. Microseconds are added only if a
        # backup with the same second already exists (two quick clicks).
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filepath = os.path.join(backup_dir, f"msms_backup_{timestamp}.json")
        if os.path.exists(backup_filepath):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
            backup_filepath = os.path.join(backup_dir, f"msms_backup_{timestamp}.json")

        # copy2 also keeps the original file's modified time.
        shutil.copy2(data_path, backup_filepath)
        logging.info(f"Data successfully backed up to {backup_filepath}")
    except OSError as e:
        logging.error(f"Failed to create backup: {e}")
        return None

    _prune_old_backups(backup_dir, keep)
    return backup_filepath


def list_backups(backup_dir=DEFAULT_BACKUP_DIR):
    """Returns the backup file paths, newest first."""
    files = glob.glob(os.path.join(backup_dir, "msms_backup_*.json"))
    return sorted(files, reverse=True)


def _prune_old_backups(backup_dir, keep):
    """Deletes the oldest backups so only the newest 'keep' remain."""
    if not keep or keep < 1:
        return
    for old in list_backups(backup_dir)[keep:]:
        try:
            os.remove(old)
            logging.info(f"Old backup removed: {old}")
        except OSError as e:
            # Not worth stopping for - the next backup will try again.
            logging.warning(f"Could not remove old backup {old}: {e}")
