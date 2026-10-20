# tests/test_schedule_manager.py - Automated tests for ScheduleManager (Fragment 5.5).
#
# Run from the project folder with:   pytest
#
# Every test follows Arrange -> Act -> Assert and checks ONE piece of logic.
# Each test gets its own brand-new data file inside pytest's tmp_path folder,
# so the tests never touch the real data/msms.json and never affect each other.

import csv
import json

import pytest

from app.schedule import ScheduleManager


# ----------------------------------------------------------------------
# Fixtures - reusable "Arrange" steps
# ----------------------------------------------------------------------

@pytest.fixture
def data_file(tmp_path):
    """Path to a data file that does not exist yet (a clean state)."""
    return str(tmp_path / "test_data.json")


@pytest.fixture
def fresh_manager(data_file):
    """A ScheduleManager with no students, teachers or courses."""
    return ScheduleManager(data_path=data_file)


@pytest.fixture
def school(fresh_manager):
    """A small school: one piano teacher, one piano course, one enrolled student."""
    m = fresh_manager
    teacher = m.add_teacher("Dr. Evelyn Keys", "Piano")
    course = m.add_course("Beginner Piano", "Piano", teacher.id)
    student = m.add_student("Alice Johnson")
    m.enrol_student(student.id, course.id)
    return m


# ----------------------------------------------------------------------
# Courses and lessons
# ----------------------------------------------------------------------

def test_create_course(fresh_manager):
    # ARRANGE: a course needs a teacher that exists.
    teacher = fresh_manager.add_teacher("Dr. Evelyn Keys", "Piano")
    # ACT
    fresh_manager.create_course("Beginner Piano", "Piano", teacher.id)
    # ASSERT
    assert len(fresh_manager.courses) == 1
    assert fresh_manager.courses[0].name == "Beginner Piano"


def test_create_course_rejects_unknown_teacher(fresh_manager):
    # ACT: teacher 99 does not exist.
    result = fresh_manager.create_course("Ghost Course", "Piano", 99)
    # ASSERT: nothing was created.
    assert result is None
    assert fresh_manager.courses == []


def test_cancel_lesson_removes_it_from_roster(school):
    # ARRANGE
    course = school.courses[0]
    school.add_lesson(course.id, "Monday", "16:00", "Room A")
    lesson_id = course.lessons[0]["lesson_id"]
    # ACT
    result = school.cancel_lesson(lesson_id, "Teacher unwell")
    # ASSERT
    assert result is True
    assert school.get_lessons_for_day("Monday") == []


def test_cancel_lesson_unknown_id_returns_false(school):
    assert school.cancel_lesson(999, "No such lesson") is False


def test_cancel_lesson_requires_reason(school):
    # ARRANGE
    course = school.courses[0]
    school.add_lesson(course.id, "Monday", "16:00", "Room A")
    lesson_id = course.lessons[0]["lesson_id"]
    # ACT
    result = school.cancel_lesson(lesson_id, "   ")
    # ASSERT: refused, and the lesson is still there.
    assert result is False
    assert len(course.lessons) == 1


# ----------------------------------------------------------------------
# Registration and check-in (PST3/PST4 logic, now under test)
# ----------------------------------------------------------------------

def test_register_new_student_enrols_in_course(school):
    # ACT: instrument typed in a different case on purpose.
    student = school.register_new_student("Bob Williams", "piano")
    # ASSERT: student created AND linked on both sides.
    assert student is not None
    course = school.courses[0]
    assert course.id in student.enrolled_course_ids
    assert student.id in course.enrolled_student_ids


def test_register_new_student_unknown_instrument_changes_nothing(school):
    # ARRANGE
    students_before = len(school.students)
    # ACT: nobody teaches the drums.
    result = school.register_new_student("Charlie", "Drums")
    # ASSERT: rejected, and no half-created student was left behind.
    assert result is None
    assert len(school.students) == students_before


def test_register_new_student_blank_name_rejected(school):
    assert school.register_new_student("   ", "Piano") is None


def test_check_in_records_attendance(school):
    # ARRANGE
    student = school.students[0]
    course = school.courses[0]
    # ACT
    result = school.check_in(student.id, course.id)
    # ASSERT
    assert result is True
    assert len(school.get_attendance_for_student(student.id)) == 1


def test_check_in_invalid_ids_rejected(school):
    assert school.check_in(999, 999) is False
    assert school.attendance_log == []


# ----------------------------------------------------------------------
# Finance (Fragment 5.1)
# ----------------------------------------------------------------------

def test_record_payment_and_history(school):
    # ARRANGE
    student_id_to_test = school.students[0].id
    # ACT: record a payment, then read the history back.
    school.record_payment(student_id_to_test, 100.00, "Credit Card")
    history = school.get_payment_history(student_id_to_test)
    # ASSERT
    assert len(history) == 1
    assert history[0]["amount"] == 100.00
    assert history[0]["method"] == "Credit Card"
    assert history[0]["student_id"] == student_id_to_test
    assert "timestamp" in history[0]


def test_get_payment_history_no_results(school):
    # ARRANGE: a student who has never paid.
    student = school.add_student("Bob Williams")
    # ACT
    history = school.get_payment_history(student.id)
    # ASSERT: an empty list, not None and not an error.
    assert history == []


def test_payment_history_only_returns_that_students_payments(school):
    # ARRANGE
    alice = school.students[0]
    bob = school.add_student("Bob Williams")
    school.record_payment(alice.id, 100, "Cash")
    school.record_payment(bob.id, 50, "Cash")
    school.record_payment(alice.id, 25.5, "E-wallet")
    # ACT
    alice_history = school.get_payment_history(alice.id)
    # ASSERT
    assert [p["amount"] for p in alice_history] == [100.0, 25.5]
    assert school.get_total_paid(alice.id) == 125.5


def test_record_payment_unknown_student_rejected(fresh_manager):
    # ACT: no students exist at all.
    result = fresh_manager.record_payment(1, 100.00, "Cash")
    # ASSERT
    assert result is None
    assert fresh_manager.finance_log == []


@pytest.mark.parametrize("bad_amount", [0, -50, "abc", None, float("nan"), float("inf")])
def test_record_payment_invalid_amount_rejected(school, bad_amount):
    # ACT
    result = school.record_payment(school.students[0].id, bad_amount, "Cash")
    # ASSERT: each bad amount is refused without crashing.
    assert result is None
    assert school.finance_log == []


def test_record_payment_blank_method_rejected(school):
    assert school.record_payment(school.students[0].id, 100, "   ") is None
    assert school.finance_log == []


def test_record_payment_accepts_numeric_string_and_rounds(school):
    # ACT: the amount arrives as text with too many decimals.
    record = school.record_payment(school.students[0].id, "49.999", "Cash")
    # ASSERT: stored as a number, rounded to cents.
    assert record["amount"] == 50.0


def test_payment_ids_are_unique_and_increasing(school):
    sid = school.students[0].id
    first = school.record_payment(sid, 10, "Cash")
    second = school.record_payment(sid, 20, "Cash")
    assert second["payment_id"] == first["payment_id"] + 1


# ----------------------------------------------------------------------
# Persistence - the finance log must survive a restart
# ----------------------------------------------------------------------

def test_payments_persist_after_reload(school, data_file):
    # ARRANGE
    sid = school.students[0].id
    school.record_payment(sid, 80, "Bank Transfer")
    # ACT: a brand-new manager reads the same file (like restarting the app).
    reloaded = ScheduleManager(data_path=data_file)
    # ASSERT
    history = reloaded.get_payment_history(sid)
    assert len(history) == 1
    assert history[0]["method"] == "Bank Transfer"
    # The next payment must not reuse the old payment id.
    new = reloaded.record_payment(sid, 10, "Cash")
    assert new["payment_id"] == history[0]["payment_id"] + 1


def test_loads_old_pst4_file_without_finance_key(data_file):
    # ARRANGE: a PST4-style file with no "finance" section.
    old_data = {
        "students": [{"id": 1, "name": "Alice", "enrolled_course_ids": []}],
        "teachers": [], "courses": [], "attendance": [],
    }
    with open(data_file, "w") as f:
        json.dump(old_data, f)
    # ACT
    m = ScheduleManager(data_path=data_file)
    # ASSERT: loads fine with an empty finance log.
    assert m.finance_log == []
    assert m.get_payment_history(1) == []


def test_corrupted_data_file_does_not_crash(data_file):
    # ARRANGE: garbage instead of JSON.
    with open(data_file, "w") as f:
        f.write("{ this is not json")
    # ACT
    m = ScheduleManager(data_path=data_file)
    # ASSERT: starts with a clean state instead of raising.
    assert m.students == []
    assert m.finance_log == []


def test_save_leaves_no_temp_file(school, data_file, tmp_path):
    # The crash-proof save writes to a .tmp file then swaps it in.
    school.add_student("Bob")
    assert not (tmp_path / "test_data.json.tmp").exists()
    with open(data_file) as f:
        assert "Bob" in f.read()


# ----------------------------------------------------------------------
# CSV export (Fragment 5.1)
# ----------------------------------------------------------------------

def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_export_finance_report(school, tmp_path):
    # ARRANGE
    sid = school.students[0].id
    school.record_payment(sid, 100, "Cash")
    school.record_payment(sid, 60, "Credit Card")
    out = tmp_path / "reports" / "finance.csv"  # folder does not exist yet
    # ACT
    rows = school.export_report("finance", str(out))
    # ASSERT
    assert rows == 2
    data = _read_csv(out)
    assert len(data) == 2
    assert data[0]["method"] == "Cash"
    assert float(data[1]["amount"]) == 60.0
    assert list(data[0].keys()) == ["payment_id", "student_id", "amount", "method", "timestamp"]


def test_export_attendance_report(school, tmp_path):
    # ARRANGE
    school.check_in(school.students[0].id, school.courses[0].id)
    out = tmp_path / "attendance.csv"
    # ACT
    rows = school.export_report("attendance", str(out))
    # ASSERT
    assert rows == 1
    assert _read_csv(out)[0]["course_id"] == str(school.courses[0].id)


def test_export_empty_log_writes_header_only(school, tmp_path):
    out = tmp_path / "finance.csv"
    assert school.export_report("finance", str(out)) == 0
    assert _read_csv(out) == []
    assert out.read_text().startswith("payment_id,student_id,amount,method,timestamp")


def test_export_unknown_kind_returns_none(school, tmp_path):
    out = tmp_path / "x.csv"
    assert school.export_report("salaries", str(out)) is None
    assert not out.exists()
