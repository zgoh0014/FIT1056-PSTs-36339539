# app/teacher.py - The Teacher and Course models.

from app.user import User


class TeacherUser(User):
    """Represents a teacher, inheriting from the base User class."""

    def __init__(self, user_id, name, speciality):
        # Reuse the parent's __init__ for id and name...
        super().__init__(user_id, name)
        # ...then add the one attribute that only a teacher has.
        self.speciality = speciality


class Course:
    """Represents a single course offered by the school, linked to a teacher.

    Course does NOT inherit from User because a course is not a person - it has
    no name/id in the "user" sense. It is a separate entity that simply lives in
    the same file as the teacher it is taught by.
    """

    def __init__(self, course_id, name, instrument, teacher_id,
                 enrolled_student_ids=None, lessons=None):
        self.id = course_id
        self.name = name
        self.instrument = instrument
        self.teacher_id = teacher_id
        # IDs of the students taking this course (the other half of the link
        # stored in StudentUser.enrolled_course_ids).
        self.enrolled_student_ids = enrolled_student_ids if enrolled_student_ids else []
        # Each lesson is a small dictionary:
        # {"lesson_id": 1, "day": "Monday", "start_time": "16:00", "room": "Room A"}
        self.lessons = lessons if lessons else []
