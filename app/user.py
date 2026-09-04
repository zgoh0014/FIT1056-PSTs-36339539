# app/user.py - The base blueprint for every person in the system.

class User:
    """A base class for all users in the system.

    Both StudentUser and TeacherUser inherit from this class, so the two
    attributes every person in the school has (an id and a name) are written
    once here instead of being repeated in each subclass.
    """

    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name

    def __str__(self):
        # Gives a readable version of any user when printed, e.g. "#1 Alice Johnson".
        return f"#{self.id} {self.name}"
