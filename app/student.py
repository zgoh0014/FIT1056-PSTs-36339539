# app/student.py - The Student model.

from app.user import User


class StudentUser(User):
    """Represents a student, inheriting from the base User class."""

    def __init__(self, user_id, name, enrolled_course_ids=None):
        # Reuse the parent's __init__ to set self.id and self.name.
        super().__init__(user_id, name)
        # A student holds only the IDs of their courses, not the Course objects
        # themselves. This keeps the JSON file simple and avoids two objects
        # pointing at each other in a loop.
        self.enrolled_course_ids = enrolled_course_ids if enrolled_course_ids else []
