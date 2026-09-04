# Music School Management System (MSMS) - Phase 1 Prototype

**Author:** Goh Zheng Qiangit add README.md

## Project Overview
This project is an in-memory Python prototype of a Music School Management System (MSMS). It allows a receptionist to register new students, enrol them in instrument classes, and look up information about students and teachers. Since this is an in-memory prototype, all data is reset when the program terminates.

## What Each Part Does
*   **Data Models (Fragment 1.1):** Defines the `Student` and `Teacher` classes to act as blueprints for the data, storing attributes like IDs, names, and enrolled instruments or specialities.
*   **Core Helper Functions (Fragment 1.2):** Contains backend functions (`add_teacher`, `list_students`, `find_teachers`, etc.) that directly manipulate the global `student_db` and `teacher_db` lists.
*   **Front Desk Functions (Fragment 1.3):** Provides higher-level operations used by the receptionist (like `front_desk_register` and `front_desk_enrol`) that chain together core helper functions to complete tasks.
*   **Main Application (Fragment 1.4):** A `while True` loop that acts as the interactive console menu, taking user input and routing it to the appropriate Front Desk functions.

## How to Run and Test the Program
1. Ensure you have Python installed on your system.
2. Open your terminal or command prompt.
3. Navigate to the root directory of this project.
4. Run the program using the command: `python MSMS.py`
5. Follow the on-screen menu prompts by entering numbers 1-5 or 'q' to quit. Test the system by registering a new student, enrolling them, and then using the lookup function to find them.

## Design Choices and Assumptions
*   **ID Generation:** Assumed that simple incrementing integers (`next_student_id`, `next_teacher_id`) are sufficient for tracking records during this temporary in-memory phase.
*   **Search Functionality:** Designed the search functions to be case-insensitive to ensure a smoother user experience when looking up names or specialities.
*   **Error Handling:** Implemented a basic `try-except` block in the main menu to catch `ValueError` exceptions if a user accidentally types letters instead of an integer for a Student ID.


## PST2: The Persistence Upgrade

### Overview
PST2 solves the "Amnesia & Chaos" problem from PST1: instead of storing students,
teachers, and attendance in memory (data lost every time the program exits),
all data is now saved to and loaded from a single JSON file, `msms.json`. This
stage also introduces full CRUD (Create, Read, Update, Delete) for students and
teachers, plus two new receptionist features: checking students into a course
and printing a student ID card.

All PST2 logic lives in `pst2_main.py`. `MSMS.py` (the PST1 prototype) is kept
in the repo for reference but is no longer used going forward.

### What Each Part Does
- **Core Persistence Engine** (`load_data`, `save_data`): Loads `app_data` from
  `msms.json` on startup, or initialises a default empty structure if the file
  doesn't exist yet. Saves the current state back to `msms.json` (formatted
  with `indent=4` for readability) after every change.
- **CRUD Operations** (`add_teacher`, `update_teacher`, `remove_teacher`,
  `update_student`, `remove_student`): Manage teacher and student records
  directly inside the `app_data` dictionary, using `**fields` keyword arguments
  so any subset of a record's fields can be updated at once.
- **Receptionist Features** (`check_in`, `print_student_card`): `check_in`
  records a timestamped attendance entry linking a student to a course.
  `print_student_card` looks up a student and writes their details to a text
  file badge (`<student_id>_card.txt`).
- **Main Loop** (`main`): Loads data on startup, presents a text menu
  (check-in, print card, update teacher, remove student, quit), and calls
  `save_data()` immediately after any operation that changes the data, so
  nothing is lost even if the program is closed unexpectedly.

### How to Run
```bash
python pst2_main.py
```
Follow the on-screen menu. Choosing `q` saves and exits; every other change is
also saved immediately after it happens.

### How to Test
The program was tested manually by running through each menu option and
inspecting `msms.json` afterwards to confirm the data persisted correctly, e.g.:
```bash
echo -e "1\n101\nMUS101\nq\n" | python pst2_main.py
cat msms.json
```
This confirms a check-in for student `101` in course `MUS101` is correctly
written to the `attendance` list with a timestamp, and that `save_data()` runs
without errors.

### Design Choices & Assumptions
- `app_data` is initialised with empty `students`/`teachers`/`attendance` lists
  and ID counters starting at `1` if `msms.json` doesn't exist yet.
- PST2's menu doesn't include an "add student" option (not required by the
  brief for this stage), so `update_student`/`remove_student`/`check_in` were
  tested by seeding or checking `msms.json` directly rather than through the
  console menu.
- `update_teacher`/`update_student` accept arbitrary keyword arguments, so any
  combination of fields can be changed in one call without needing a separate
  function per field.

## PST3: The Architectural Redesign (OOP)

### Overview
PST3 solves the "Messy & Unscalable" problem of the procedural `pst2_main.py`:
a single file holding a global `app_data` dictionary, where every function was
free to reach in and change anything. PST3 rebuilds the same system as an
Object-Oriented application split into three layers:

| Layer | Files | Responsibility |
| --- | --- | --- |
| **Model** | `app/user.py`, `app/student.py`, `app/teacher.py` | Blueprints for the things the school has: users, students, teachers, courses. |
| **Controller** | `app/schedule.py` | `ScheduleManager` — all business logic and all reading/writing of the data file. |
| **View** | `main.py` | Menus, input, and formatting. Holds no data and no business logic. |

Data now lives in `data/msms.json` and is loaded into real Python objects at
startup, instead of being passed around as raw dictionaries.

### Project Structure
```
FIT1056-PSTs-36339539/
├── main.py             # View layer + entry point
├── app/
│   ├── __init__.py     # Marks app/ as a Python package so 'from app.x import y' works
│   ├── user.py         # User (base class)
│   ├── student.py      # StudentUser(User)
│   ├── teacher.py      # TeacherUser(User) and Course
│   └── schedule.py     # ScheduleManager (the controller / "brain")
├── data/
│   └── msms.json       # All persisted data
├── pst2_main.py        # PST2 (kept for reference, no longer used)
└── MSMS.py             # PST1 (kept for reference, no longer used)
```

### What Each Part Does

**Fragment 3.1 — The Model Layer (`app/user.py`, `app/student.py`, `app/teacher.py`)**
- `User` is the base class holding the two attributes every person has: `id` and `name`.
- `StudentUser(User)` calls `super().__init__()` to reuse that, then adds
  `enrolled_course_ids`.
- `TeacherUser(User)` does the same, then adds `speciality`.
- `Course` is defined in `teacher.py` alongside the teacher who runs it. It does
  **not** inherit from `User`, because a course is not a person — it holds
  `instrument`, `teacher_id`, `enrolled_student_ids`, and a list of `lessons`.

**Fragment 3.2 — The Controller (`app/schedule.py`)**
- `ScheduleManager.__init__` sets up empty `students`, `teachers`, `courses`,
  `attendance_log` lists plus the ID counters, then calls `_load_data()`.
- `_load_data()` reads the raw dictionaries out of the JSON file and *rebuilds
  them into objects* (`StudentUser`, `TeacherUser`, `Course`). This is the link
  between the flat file and the object model.
- `attendance_log` is loaded with `data.get("attendance", [])`, so an older data
  file without that key still loads instead of raising a `KeyError`.
- `_save_data()` does the reverse: `s.__dict__` turns each object back into a
  plain dictionary that `json.dump()` can write.
- Full CRUD lives here: `add/update/remove` for students, teachers and courses,
  plus `add_lesson`, `enrol_student`, `unenrol_student` and `switch_course`.

**Fragment 3.3 — Core Business Logic (`check_in`)**
- Validates that both the student and the course exist before recording
  anything, and warns (without blocking) if the student is not enrolled.
- Appends a timestamped record to `self.attendance_log` and calls `_save_data()`
  so the check-in survives the program closing.

**Fragment 3.4 — The View (`main.py`)**
- Creates **one** `ScheduleManager` and passes it to every view function.
- `front_desk_daily_roster(manager, day)` asks the manager for the day's lessons
  and prints them as a table; `switch_course(manager, ...)` delegates the whole
  move to the manager.
- `print_student_card` writes the badge file here rather than in the manager,
  because formatting output is a View responsibility.

### How to Run
```bash
python main.py
```
Run it from the project root. (`app/schedule.py` builds the path to
`data/msms.json` from its own file location, so it also works if you run
`python /full/path/to/main.py` from somewhere else.)

### How to Test
The program was tested by running every menu option and inspecting
`data/msms.json` afterwards. For example, adding a student, enrolling them,
checking them in, and switching their course:
```bash
printf '5\nCarol Tan\n15\n3\n101\n17\n3\n101\n16\n3\n101\n103\n2\nq\n' | python main.py
```
Then confirm the change persisted by starting the program again and choosing
option `2` (List students) — Carol appears with ID 3, enrolled in Intermediate
Piano, and the check-in is in the `attendance` list of `data/msms.json`.

Error paths were tested the same way: removing a student who does not exist,
removing a teacher who still teaches a course, enrolling a student twice in the
same course, and typing letters where a number is expected. All of these print
an error message and return to the menu instead of crashing.

### Design Choices & Assumptions
- **Objects hold IDs, not other objects.** A student stores
  `enrolled_course_ids`, not a list of `Course` objects. This keeps the JSON
  simple to write with `__dict__` and avoids two objects referencing each other
  in a loop, which `json.dump()` cannot serialise.
- **The link is kept in sync on both sides.** `enrol_student` updates both
  `student.enrolled_course_ids` and `course.enrolled_student_ids`, and the
  `remove_*` methods clean up the other side, so the data never ends up with a
  course pointing at a deleted student.
- **Save after every change.** Each method that changes data calls
  `_save_data()` itself, so there is no "unsaved work" to lose. This is why
  `main.py` needs no final save on quit, unlike PST2.
- **Leading underscore = internal.** `_load_data` and `_save_data` are marked
  private by convention: they are the manager's own business, and `main.py`
  should never call them directly.
- **`switch_course` validates before it changes anything.** Both course IDs are
  checked first, so a failed switch can never leave a student unenrolled from
  the old course but not enrolled in the new one.
- **Attendance records stay plain dictionaries.** An attendance record has no
  behaviour of its own, so it does not need a class.
- **ID counters are stored in the JSON** (`next_student_id`, etc.). If they are
  missing from the file, `_load_data` works them out from the highest existing
  ID so a duplicate ID can never be handed out.
- **New in PST3:** `data/msms.json` is the first data file committed to the
  repo, so the program has sample students, teachers, courses and lessons to
  demonstrate with. PST2 generated its `msms.json` at runtime.
