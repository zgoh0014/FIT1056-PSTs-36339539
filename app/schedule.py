# app/schedule.py - The Controller layer ("the brain" of the application).
#
# Everything that changes data goes through ScheduleManager. main.py (the View)
# never touches the JSON file or the object lists directly - it only calls the
# methods below. That separation is the whole point of the PST3 redesign.

import os
import json
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
        # ID counters, so every new record gets a unique id.
        self.next_student_id = 1
        self.next_teacher_id = 1
        self.next_course_id = 101
        self.next_lesson_id = 1
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

        # If the file has no saved counters, work them out from the highest id
        # already in use so we never hand out a duplicate id.
        self.next_student_id = data.get("next_student_id", self._next_id(self.students, 1))
        self.next_teacher_id = data.get("next_teacher_id", self._next_id(self.teachers, 1))
        self.next_course_id = data.get("next_course_id", self._next_id(self.courses, 101))
        self.next_lesson_id = data.get("next_lesson_id", self._next_lesson_id())

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
            "next_student_id": self.next_student_id,
            "next_teacher_id": self.next_teacher_id,
            "next_course_id": self.next_course_id,
            "next_lesson_id": self.next_lesson_id,
        }
        with open(self.data_path, "w") as f:
            json.dump(data_to_save, f, indent=4)

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
    # Read-only queries - these return data for main.py to format and print
    # ------------------------------------------------------------------

    def get_lessons_for_day(self, day):
        """Returns a list of (course, lesson) pairs happening on the given day.

        The manager does the searching; main.py does the printing.
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
