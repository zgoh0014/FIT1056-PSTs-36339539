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