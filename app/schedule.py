# app/schedule.py - The Controller layer ("the brain" of the application).
#
# Everything that changes data goes through ScheduleManager. The View (the
# Streamlit GUI in gui/ since PST4) never touches the JSON file or changes the
# object lists directly - it only calls the methods below. That separation is
# the whole point of the PST3 redesign, and it is why PST4 could swap the text
# console for a GUI without rewriting any business logic.
#
# PST5 adds the finance engine (payments + CSV reports), cancel_lesson, and
# logging of every important business event (see app/admin_utils.py).

import os
import csv
import json
import math
import logging
import datetime

from app.student import StudentUser
from app.teacher import TeacherUser, Course

# Work out the path to data/msms.json relative to THIS file, so the program runs
# correctly no matter which folder the terminal happens to be in.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_PATH = os.path.join(BASE_DIR, "data", "msms.json")


class ScheduleManager:
    """The main controller for all business logic and data handling."""

    def __init__(self, data_path=DEFAULT_DATA_PATH):
        self.data_path = data_path
        # The manager's state: lists of real objects, not raw dictionaries.
        self.students = []
        self.teachers = []
        self.courses = []
        # The attendance log stays a plain list of dictionaries - an attendance
        # record has no behaviour of its own, so it does not need a class.
        self.attendance_log = []
        # PST5: every payment the front desk takes. Also a list of plain
        # dictionaries, for the same reason as the attendance log.
        self.finance_log = []
        # ID counters, so every new record gets a unique id.
        self.next_student_id = 1
        self.next_teacher_id = 1
        self.next_course_id = 101
        self.next_lesson_id = 1
        self.next_payment_id = 1
        # Fill all of the above from the JSON file the moment the manager exists.
        self._load_data()

    # ------------------------------------------------------------------
    # Persistence (Fragment 3.2)
    # ------------------------------------------------------------------

    def _load_data(self):
        """Loads data from the JSON file and turns the raw dictionaries into objects."""
        try:
            with open(self.data_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print("Data file not found. Starting with a clean state.")
            return
        except json.JSONDecodeError:
            # A corrupted file should not crash the whole program.
            print("Data file is not valid JSON. Starting with a clean state.")
            logging.error(f"Data file {self.data_path} is not valid JSON - started with a clean state.")
            return

        # Rebuild each student dictionary into a StudentUser object.
        for s in data.get("students", []):
            self.students.append(
                StudentUser(s["id"], s["name"], s.get("enrolled_course_ids", []))
            )

        # Rebuild each teacher dictionary into a TeacherUser object.
        for t in data.get("teachers", []):
            self.teachers.append(
                TeacherUser(t["id"], t["name"], t.get("speciality", ""))
            )

        # Rebuild each course dictionary into a Course object.
        for c in data.get("courses", []):
            self.courses.append(
                Course(
                    c["id"],
                    c["name"],
                    c.get("instrument", ""),
                    c.get("teacher_id"),
                    c.get("enrolled_student_ids", []),
                    c.get("lessons", []),
                )
            )

        # .get() with a default means an older msms.json without an "attendance"
        # key still loads instead of raising a KeyError.
        self.attendance_log = data.get("attendance", [])
        # Same idea for the finance log: a PST4 data file has no "finance" key,
        # so it loads as "no payments yet" instead of crashing.
        self.finance_log = data.get("finance", [])

        # If the file has no saved counters, work them out from the highest id
        # already in use so we never hand out a duplicate id.
        self.next_student_id = data.get("next_student_id", self._next_id(self.students, 1))
        self.next_teacher_id = data.get("next_teacher_id", self._next_id(self.teachers, 1))
        self.next_course_id = data.get("next_course_id", self._next_id(self.courses, 101))
        self.next_lesson_id = data.get("next_lesson_id", self._next_lesson_id())
        self.next_payment_id = data.get(
            "next_payment_id",
            max((p.get("payment_id", 0) for p in self.finance_log), default=0) + 1,
        )

    def _save_data(self):
        """Converts the object lists back into dictionaries and writes them to JSON."""
        data_to_save = {
            # __dict__ gives every attribute of an object as a dictionary, which
            # is exactly the shape json.dump() needs.
            "students": [s.__dict__ for s in self.students],
            "teachers": [t.__dict__ for t in self.teachers],
            "courses": [c.__dict__ for c in self.courses],
            # Already a list of plain dictionaries, so no conversion is needed.
            "attendance": self.attendance_log,
            "finance": self.finance_log,
            "next_student_id": self.next_student_id,
            "next_teacher_id": self.next_teacher_id,
            "next_course_id": self.next_course_id,
            "next_lesson_id": self.next_lesson_id,
            "next_payment_id": self.next_payment_id,
        }
        # Crash-proof save: write to a temporary file first, then swap it into
        # place in one step. If the program dies half-way through writing, the
        # real msms.json is untouched instead of being left half-written.
        folder = os.path.dirname(self.data_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        temp_path = self.data_path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data_to_save, f, indent=4)
        os.replace(temp_path, self.data_path)

    # --- small private helpers used only while loading ---

    def _next_id(self, items, start):
        """Returns one more than the highest id in a list, or 'start' if it is empty."""
        if not items:
            return start
        return max(item.id for item in items) + 1

    def _next_lesson_id(self):
        """Returns one more than the highest lesson_id across every course."""
        highest = 0
        for course in self.courses:
            for lesson in course.lessons:
                highest = max(highest, lesson.get("lesson_id", 0))
        return highest + 1

    # ------------------------------------------------------------------
    # Lookup helpers - used by almost every method below
    # ------------------------------------------------------------------

    def find_student_by_id(self, student_id):
        """Returns the StudentUser with this id, or None if there isn't one."""
        for student in self.students:
            if student.id == student_id:
                return student
        return None

    def find_teacher_by_id(self, teacher_id):
        """Returns the TeacherUser with this id, or None if there isn't one."""
        for teacher in self.teachers:
            if teacher.id == teacher_id:
                return teacher
        return None

    def find_course_by_id(self, course_id):
        """Returns the Course with this id, or None if there isn't one."""
        for course in self.courses:
            if course.id == course_id:
                return course
        return None

    # ------------------------------------------------------------------
    # Student CRUD
    # ------------------------------------------------------------------

    def add_student(self, name):
        """Creates a new student and saves. Returns the new StudentUser."""
        student = StudentUser(self.next_student_id, name)
        self.students.append(student)
        self.next_student_id += 1
        self._save_data()
        print(f"Success: Student '{name}' added with ID {student.id}.")
        return student

    def update_student(self, student_id, name):
        """Renames an existing student."""
        student = self.find_student_by_id(student_id)
        if not student:
            print(f"Error: Student with ID {student_id} not found.")
            return False
        student.name = name
        self._save_data()
        print(f"Success: Student {student_id} renamed to '{name}'.")
        return True

    def remove_student(self, student_id):
        """Deletes a student and unenrols them from every course first."""
        student = self.find_student_by_id(student_id)
        if not student:
            print(f"Error: Student with ID {student_id} not found.")
            return False
        # Clean up the other side of the link, otherwise courses would keep
        # pointing at a student that no longer exists.
        for course in self.courses:
            if student_id in course.enrolled_student_ids:
                course.enrolled_student_ids.remove(student_id)
        self.students.remove(student)
        self._save_data()
        print(f"Success: Student {student_id} removed.")
        return True

    # ------------------------------------------------------------------
    # Teacher CRUD
    # ------------------------------------------------------------------

    def add_teacher(self, name, speciality):
        """Creates a new teacher and saves. Returns the new TeacherUser."""
        teacher = TeacherUser(self.next_teacher_id, name, speciality)
        self.teachers.append(teacher)
        self.next_teacher_id += 1
        self._save_data()
        print(f"Success: Teacher '{name}' added with ID {teacher.id}.")
        return teacher

    def update_teacher(self, teacher_id, name=None, speciality=None):
        """Updates a teacher's name and/or speciality. Blank entries are ignored."""
        teacher = self.find_teacher_by_id(teacher_id)
        if not teacher:
            print(f"Error: Teacher with ID {teacher_id} not found.")
            return False
        if name:
            teacher.name = name
        if speciality:
            teacher.speciality = speciality
        self._save_data()
        print(f"Success: Teacher {teacher_id} updated.")
        return True

    def remove_teacher(self, teacher_id):
        """Deletes a teacher, but refuses if they still teach a course."""
        teacher = self.find_teacher_by_id(teacher_id)
        if not teacher:
            print(f"Error: Teacher with ID {teacher_id} not found.")
            return False
        # A course with no teacher would break the daily roster, so block this.
        taught = [c.name for c in self.courses if c.teacher_id == teacher_id]
        if taught:
            print(f"Error: Cannot remove teacher {teacher_id} - still teaching: {', '.join(taught)}.")
            return False
        self.teachers.remove(teacher)
        self._save_data()
        print(f"Success: Teacher {teacher_id} removed.")
        return True

    # ------------------------------------------------------------------
    # Course CRUD
    # ------------------------------------------------------------------

    def add_course(self, name, instrument, teacher_id):
        """Creates a new course, as long as the teacher exists."""
        if not self.find_teacher_by_id(teacher_id):
            print(f"Error: Cannot create course - teacher {teacher_id} not found.")
            return None
        course = Course(self.next_course_id, name, instrument, teacher_id)
        self.courses.append(course)
        self.next_course_id += 1
        self._save_data()
        print(f"Success: Course '{name}' added with ID {course.id}.")
        return course

    def create_course(self, name, instrument, teacher_id):
        """Same as add_course - the name used by the PST5 test template."""
        return self.add_course(name, instrument, teacher_id)

    def update_course(self, course_id, name=None, instrument=None, teacher_id=None):
        """Updates a course's details. Blank entries are ignored."""
        course = self.find_course_by_id(course_id)
        if not course:
            print(f"Error: Course with ID {course_id} not found.")
            return False
        if name:
            course.name = name
        if instrument:
            course.instrument = instrument
        if teacher_id is not None:
            if not self.find_teacher_by_id(teacher_id):
                print(f"Error: Teacher {teacher_id} not found. Teacher not changed.")
            else:
                course.teacher_id = teacher_id
        self._save_data()
        print(f"Success: Course {course_id} updated.")
        return True

    def remove_course(self, course_id):
        """Deletes a course and removes it from every enrolled student."""
        course = self.find_course_by_id(course_id)
        if not course:
            print(f"Error: Course with ID {course_id} not found.")
            return False
        for student in self.students:
            if course_id in student.enrolled_course_ids:
                student.enrolled_course_ids.remove(course_id)
        self.courses.remove(course)
        self._save_data()
        print(f"Success: Course {course_id} removed.")
        return True

    def add_lesson(self, course_id, day, start_time, room):
        """Adds a timetabled lesson to a course, so it shows up on the daily roster."""
        course = self.find_course_by_id(course_id)
        if not course:
            print(f"Error: Course with ID {course_id} not found.")
            return False
        lesson = {
            "lesson_id": self.next_lesson_id,
            "day": day,
            "start_time": start_time,
            "room": room,
        }
        course.lessons.append(lesson)
        self.next_lesson_id += 1
        self._save_data()
        print(f"Success: Lesson added to '{course.name}' on {day} at {start_time}.")
        return True

    def cancel_lesson(self, lesson_id, reason):
        """Removes a timetabled lesson from its course (PST5).

        The reason is required because a cancellation affects students and
        teachers - it is written to the log so the school can see later why a
        class disappeared from the roster.
        """
        reason = str(reason).strip()
        if not reason:
            print("Error: Please give a reason for cancelling the lesson.")
            return False
        for course in self.courses:
            for lesson in course.lessons:
                if lesson.get("lesson_id") == lesson_id:
                    course.lessons.remove(lesson)
                    self._save_data()
                    print(f"Success: Lesson {lesson_id} of '{course.name}' cancelled.")
                    # WARNING rather than INFO: a cancellation is something an
                    # administrator may need to follow up on.
                    logging.warning(
                        f"Lesson ID {lesson_id} ({course.name}, {lesson.get('day')} "
                        f"{lesson.get('start_time')}) was cancelled. Reason: {reason}"
                    )
                    return True
        print(f"Error: Lesson with ID {lesson_id} not found.")
        return False

    # ------------------------------------------------------------------
    # Enrolment
    # ------------------------------------------------------------------

    def enrol_student(self, student_id, course_id):
        """Links a student and a course together, updating BOTH sides of the link."""
        student = self.find_student_by_id(student_id)
        course = self.find_course_by_id(course_id)
        if not student or not course:
            print("Error: Enrolment failed. Invalid Student or Course ID.")
            return False
        if course_id in student.enrolled_course_ids:
            print(f"Error: {student.name} is already enrolled in '{course.name}'.")
            return False
        student.enrolled_course_ids.append(course_id)
        course.enrolled_student_ids.append(student_id)
        self._save_data()
        print(f"Success: {student.name} enrolled in '{course.name}'.")
        return True

    def unenrol_student(self, student_id, course_id):
        """Breaks the link between a student and a course on both sides."""
        student = self.find_student_by_id(student_id)
        course = self.find_course_by_id(course_id)
        if not student or not course:
            print("Error: Unenrolment failed. Invalid Student or Course ID.")
            return False
        if course_id not in student.enrolled_course_ids:
            print(f"Error: {student.name} is not enrolled in '{course.name}'.")
            return False
        student.enrolled_course_ids.remove(course_id)
        if student_id in course.enrolled_student_ids:
            course.enrolled_student_ids.remove(student_id)
        self._save_data()
        print(f"Success: {student.name} unenrolled from '{course.name}'.")
        return True

    def switch_course(self, student_id, from_course_id, to_course_id):
        """Moves a student from one course to another.

        Both IDs are checked BEFORE anything changes, so a failed switch can
        never leave the student unenrolled from the old course but not enrolled
        in the new one.
        """
        student = self.find_student_by_id(student_id)
        from_course = self.find_course_by_id(from_course_id)
        to_course = self.find_course_by_id(to_course_id)

        if not student or not from_course or not to_course:
            print("Error: Switch failed. Invalid Student or Course ID.")
            return False
        if from_course_id not in student.enrolled_course_ids:
            print(f"Error: {student.name} is not enrolled in '{from_course.name}'.")
            return False
        if to_course_id in student.enrolled_course_ids:
            print(f"Error: {student.name} is already enrolled in '{to_course.name}'.")
            return False

        self.unenrol_student(student_id, from_course_id)
        self.enrol_student(student_id, to_course_id)
        print(f"Success: {student.name} switched from '{from_course.name}' to '{to_course.name}'.")
        return True

    # ------------------------------------------------------------------
    # Core business logic (Fragment 3.3)
    # ------------------------------------------------------------------

    def check_in(self, student_id, course_id):
        """Records a student's attendance for a course after validation."""
        student = self.find_student_by_id(student_id)
        course = self.find_course_by_id(course_id)

        if not student or not course:
            print("Error: Check-in failed. Invalid Student or Course ID.")
            return False

        # Not a hard error - the front desk may still want to record a visitor
        # sitting in on a class - but worth flagging to the receptionist.
        if course_id not in student.enrolled_course_ids:
            print(f"Warning: {student.name} is not enrolled in '{course.name}'.")

        timestamp = datetime.datetime.now().isoformat()
        check_in_record = {
            "student_id": student_id,
            "course_id": course_id,
            "timestamp": timestamp,
        }
        self.attendance_log.append(check_in_record)
        self._save_data()
        print(f"Success: Student {student.name} checked into {course.name}.")
        logging.info(f"Check-in: student ID {student_id} ({student.name}) into course ID {course_id} ({course.name}).")
        return True

    # ------------------------------------------------------------------
    # Front-desk registration (PST4 - called by the GUI's Register form)
    # ------------------------------------------------------------------

    def find_teacher_for_instrument(self, instrument):
        """Returns the first teacher whose speciality matches the instrument, or None.

        The comparison ignores case and surrounding spaces, so "piano", "Piano"
        and " PIANO " all match a teacher whose speciality is "Piano".
        """
        wanted = instrument.strip().lower()
        for teacher in self.teachers:
            if teacher.speciality.strip().lower() == wanted:
                return teacher
        return None

    def register_new_student(self, name, instrument):
        """Registers a new student AND enrols them in a course for their instrument.

        This is the one-step "walk-in registration" the receptionist uses.
        Returns the new StudentUser, or None if registration was not possible.

        Like switch_course, everything is validated BEFORE any data changes, so
        a failed registration never leaves a half-created student in the file.
        """
        name = name.strip()
        instrument = instrument.strip()
        if not name or not instrument:
            print("Error: Registration failed. Name and instrument are both required.")
            logging.warning("Registration rejected: name or instrument was blank.")
            return None

        # 1. The school must have a teacher for this instrument.
        teacher = self.find_teacher_for_instrument(instrument)
        if not teacher:
            print(f"Error: Registration failed. No teacher available for '{instrument}'.")
            logging.warning(f"Registration of '{name}' rejected: no teacher for '{instrument}'.")
            return None

        # 2. Pick the course to put them in. Courses are kept in id order and the
        #    lowest id for an instrument is its entry-level course (e.g. 101
        #    "Beginner Piano" before 103 "Intermediate Piano"), which is the right
        #    place for a brand-new student.
        course = None
        for c in self.courses:
            if c.instrument.strip().lower() == instrument.lower():
                course = c
                break

        # 3. Only now do we change data.
        if course is None:
            # A teacher exists but no course has been set up yet - open a beginner
            # course with that teacher rather than turning the student away.
            course = self.add_course(f"Beginner {teacher.speciality}", teacher.speciality, teacher.id)

        student = self.add_student(name)
        self.enrol_student(student.id, course.id)
        print(f"Success: Registered {student.name} (ID {student.id}) into '{course.name}'.")
        logging.info(f"New student registered: {student.name} (ID {student.id}) into '{course.name}' (ID {course.id}).")
        return student

    # ------------------------------------------------------------------
    # Read-only queries - these return data for the View (now the GUI) to display
    # ------------------------------------------------------------------

    def get_lessons_for_day(self, day):
        """Returns a list of (course, lesson) pairs happening on the given day.

        The manager does the searching; the View decides how to display it.
        """
        found = []
        for course in self.courses:
            for lesson in course.lessons:
                if lesson.get("day", "").lower() == day.lower():
                    found.append((course, lesson))
        # Sort by start time so the roster reads top-to-bottom like a timetable.
        found.sort(key=lambda pair: pair[1].get("start_time", ""))
        return found

    def get_courses_for_student(self, student_id):
        """Returns the Course objects a student is enrolled in."""
        student = self.find_student_by_id(student_id)
        if not student:
            return []
        return [c for c in self.courses if c.id in student.enrolled_course_ids]

    def get_attendance_for_student(self, student_id):
        """Returns every attendance record belonging to one student."""
        return [r for r in self.attendance_log if r["student_id"] == student_id]

    def search_students(self, query):
        """Returns the students matching a search box entry.

        - A blank query returns every student (the full directory).
        - A number is treated as a student ID, e.g. "2".
        - Anything else is a case-insensitive partial name match, e.g. "ali"
          finds "Alice Johnson".
        """
        query = query.strip()
        if not query:
            return list(self.students)
        if query.isdigit():
            student = self.find_student_by_id(int(query))
            return [student] if student else []
        return [s for s in self.students if query.lower() in s.name.lower()]

    def get_attendance_for_date(self, date_str):
        """Returns the attendance records for one date ("YYYY-MM-DD"), newest first.

        Timestamps are stored as ISO strings (e.g. "2026-10-05T16:02:45"), so the
        first 10 characters are the date.
        """
        records = [r for r in self.attendance_log if r.get("timestamp", "")[:10] == date_str]
        return sorted(records, key=lambda r: r["timestamp"], reverse=True)

    # ------------------------------------------------------------------
    # Finance & reporting (PST5 - Fragment 5.1)
    # ------------------------------------------------------------------

    def record_payment(self, student_id, amount, method):
        """Adds a payment record to the finance log and saves it.

        Returns the new payment dictionary, or None if the payment was rejected.
        Everything is validated BEFORE the log is touched, so a bad entry can
        never end up in the file.
        """
        # 1. The student must exist - money cannot be booked against nobody.
        student = self.find_student_by_id(student_id)
        if not student:
            print(f"Error: Payment rejected. Student with ID {student_id} not found.")
            logging.warning(f"Payment rejected: student ID {student_id} not found.")
            return None

        # 2. The amount must be a real, positive number. float() turns "50" or
        #    50 into 50.0; anything that is not a number raises an error that we
        #    catch here instead of letting it crash the program. NaN and
        #    infinity are numbers to Python but not to an accountant.
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            print(f"Error: Payment rejected. '{amount}' is not a valid amount.")
            logging.warning(f"Payment rejected for student ID {student_id}: invalid amount {amount!r}.")
            return None
        if math.isnan(amount) or math.isinf(amount) or amount <= 0:
            print("Error: Payment rejected. The amount must be greater than zero.")
            logging.warning(f"Payment rejected for student ID {student_id}: amount {amount} is not positive.")
            return None

        # 3. The method must not be blank, otherwise the report is useless.
        method = str(method).strip() if method is not None else ""
        if not method:
            print("Error: Payment rejected. Please enter a payment method.")
            logging.warning(f"Payment rejected for student ID {student_id}: no payment method given.")
            return None

        # Money is stored to 2 decimal places (cents) so 0.1 + 0.2 style
        # floating point noise never shows up on a receipt.
        payment_record = {
            "payment_id": self.next_payment_id,
            "student_id": student_id,
            "amount": round(amount, 2),
            "method": method,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        self.finance_log.append(payment_record)
        self.next_payment_id += 1
        self._save_data()
        print(f"Payment of {payment_record['amount']:.2f} for student {student_id} recorded.")
        logging.info(
            f"Payment #{payment_record['payment_id']} of {payment_record['amount']:.2f} "
            f"({method}) recorded for student ID {student_id} ({student.name})."
        )
        return payment_record

    def get_payment_history(self, student_id):
        """Returns a list of all payments for a given student, oldest first."""
        return [p for p in self.finance_log if p.get("student_id") == student_id]

    def get_total_paid(self, student_id):
        """Returns the total a student has paid so far (0.0 if nothing)."""
        return round(sum(p.get("amount", 0) for p in self.get_payment_history(student_id)), 2)

    # Which list and which columns each report kind exports. Kept in one
    # dictionary so adding a new report type is a one-line change.
    REPORT_KINDS = {
        "finance": ("finance_log", ["payment_id", "student_id", "amount", "method", "timestamp"]),
        "attendance": ("attendance_log", ["student_id", "course_id", "timestamp"]),
    }

    def export_report(self, kind, out_path):
        """Exports the finance or attendance log to a CSV file.

        Returns the number of rows written, or None if the export failed
        (unknown report type, or the file could not be written - e.g. it is
        open in Excel on Windows).
        """
        print(f"Exporting {kind} report to {out_path}...")
        if kind not in self.REPORT_KINDS:
            print(f"Error: Unknown report type '{kind}'. Use one of: {', '.join(self.REPORT_KINDS)}.")
            logging.warning(f"Export rejected: unknown report type '{kind}'.")
            return None

        list_name, headers = self.REPORT_KINDS[kind]
        data_to_export = getattr(self, list_name)

        try:
            folder = os.path.dirname(out_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            # newline="" stops Windows adding a blank line between rows.
            # extrasaction="ignore" skips any extra keys a record may have, and
            # restval="" fills in any missing ones, so an odd old record cannot
            # break the whole export.
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore", restval="")
                writer.writeheader()
                writer.writerows(data_to_export)
        except OSError as e:
            print(f"Error: Could not write the report: {e}")
            logging.error(f"Export of {kind} report to {out_path} failed: {e}")
            return None

        print(f"Success: {len(data_to_export)} row(s) exported.")
        logging.info(f"Exported {kind} report ({len(data_to_export)} rows) to {out_path}.")
        return len(data_to_export)
