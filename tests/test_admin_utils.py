# tests/test_admin_utils.py - Tests for logging and backups (Fragments 5.3 / 5.4).

import os
import json
import logging

import pytest

from app.admin_utils import init_logger, backup_data, list_backups
from app.schedule import ScheduleManager


@pytest.fixture
def clean_root_logger():
    """Removes any handlers a test adds, so tests do not leak into each other."""
    root = logging.getLogger()
    before = list(root.handlers)
    yield
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            handler.close()


# ----------------------------------------------------------------------
# Backups
# ----------------------------------------------------------------------

def test_backup_creates_timestamped_copy(tmp_path):
    # ARRANGE
    data = tmp_path / "msms.json"
    data.write_text(json.dumps({"students": []}))
    backup_dir = tmp_path / "backups"  # does not exist yet
    # ACT
    path = backup_data(str(data), str(backup_dir))
    # ASSERT: the folder was created and the copy is identical.
    assert path is not None
    assert os.path.basename(path).startswith("msms_backup_")
    with open(path) as f:
        assert f.read() == data.read_text()


def test_backup_missing_data_file_returns_none(tmp_path):
    # ACT: nothing to back up - must not raise.
    result = backup_data(str(tmp_path / "missing.json"), str(tmp_path / "backups"))
    # ASSERT
    assert result is None


def test_two_quick_backups_do_not_overwrite_each_other(tmp_path):
    data = tmp_path / "msms.json"
    data.write_text("{}")
    first = backup_data(str(data), str(tmp_path / "b"))
    second = backup_data(str(data), str(tmp_path / "b"))
    assert first != second
    assert len(list_backups(str(tmp_path / "b"))) == 2


def test_old_backups_are_pruned(tmp_path):
    # ARRANGE
    data = tmp_path / "msms.json"
    data.write_text("{}")
    backup_dir = str(tmp_path / "b")
    # ACT: five backups but only keep three.
    for _ in range(5):
        backup_data(str(data), backup_dir, keep=3)
    # ASSERT
    assert len(list_backups(backup_dir)) == 3


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def test_init_logger_writes_business_events(tmp_path, clean_root_logger):
    # ARRANGE
    log_file = tmp_path / "test.log"
    init_logger(str(log_file))
    m = ScheduleManager(data_path=str(tmp_path / "data.json"))
    student = m.add_student("Alice")
    # ACT: a payment is a key business event that must be logged.
    m.record_payment(student.id, 75, "Cash")
    # ASSERT
    text = log_file.read_text()
    assert "Payment #1 of 75.00 (Cash) recorded for student ID 1" in text
    assert " - INFO - " in text


def test_rejected_payment_is_logged_as_warning(tmp_path, clean_root_logger):
    log_file = tmp_path / "test.log"
    init_logger(str(log_file))
    m = ScheduleManager(data_path=str(tmp_path / "data.json"))
    m.record_payment(42, 75, "Cash")  # no such student
    assert "WARNING - Payment rejected: student ID 42 not found." in log_file.read_text()


def test_init_logger_twice_does_not_duplicate_lines(tmp_path, clean_root_logger):
    # ARRANGE: Streamlit re-runs main.py on every click, so this happens a lot.
    log_file = tmp_path / "test.log"
    init_logger(str(log_file))
    init_logger(str(log_file))
    # ACT
    logging.info("hello once")
    # ASSERT
    assert log_file.read_text().count("hello once") == 1
