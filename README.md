# Music School Management System (MSMS) - Phase 1 Prototype

**Author:** Goh Zheng Qian

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


## PST4: The Modern User Experience (GUI)

### Overview
PST4 solves the "Clunky & Unfriendly" problem of the PST3 text console, where
the receptionist had to remember menu numbers and type raw IDs. The console is
replaced by a **Streamlit** web GUI with a sidebar menu, search boxes, forms,
dropdowns and tables.

Because PST3 already separated the layers, the GUI is simply a **new View**.
It sits on top of the same `ScheduleManager`, so the models and the data file
did not change. The controller only gained four methods the new screens
needed (listed below).

| Layer | Files | Change in PST4 |
| --- | --- | --- |
| **Model** | `app/user.py`, `app/student.py`, `app/teacher.py` | None |
| **Controller** | `app/schedule.py` | Added `register_new_student`, `find_teacher_for_instrument`, `search_students`, `get_attendance_for_date` |
| **View** | `gui/` (new), `main.py` | Console menu replaced by Streamlit pages; `main.py` is now only a launcher |

### Project Structure
```
FIT1056-PSTs-36339539/
├── main.py                 # Launcher only - starts the GUI
├── requirements.txt        # streamlit, pandas
├── gui/                    # NEW: the View layer
│   ├── __init__.py
│   ├── main_dashboard.py   # launch(): page setup, session state, sidebar navigation
│   ├── student_pages.py    # Student Management page (search + registration)
│   └── roster_pages.py     # Daily Roster page (timetable + check-in + today's log)
├── app/                    # Model + Controller (from PST3)
│   ├── user.py, student.py, teacher.py
│   └── schedule.py         # ScheduleManager
├── data/
│   └── msms.json
└── PST2/ ... PST4/         # Brief, rubric and templates for each stage
```

### What Each Part Does

**Fragment 4.1: Launcher & Main Dashboard (`main.py`, `gui/main_dashboard.py`)**
- `main.py` does one thing: call `launch()`. If it is started with plain
  `python main.py` instead of `streamlit run main.py`, it starts the Streamlit
  server itself rather than printing a page of warnings.
- `launch()` sets the page layout and builds **one** `ScheduleManager`, stored in
  `st.session_state`. Streamlit re-runs the whole script on every click, and
  session state is what stops the manager (and the JSON file read) from being
  recreated each time.
- The sidebar holds the page menu (Student Management, Daily Roster,
  Payments stub) and a small "school at a glance" panel with student, teacher
  and course counts.

**Fragment 4.2: Student Management (`gui/student_pages.py`)**
- **Find a Student**: a search box that matches partial names (case-insensitive)
  or an exact student ID. Results show in a table with each student's courses
  and number of check-ins. A blank search lists every student.
- **Register New Student**: name + first instrument. Submitting calls
  `manager.register_new_student(name, instrument)`, which:
  1. checks a teacher exists whose speciality matches the instrument
     (`"piano"`, `"Piano"` and `" PIANO "` all match),
  2. picks the entry-level course for that instrument (lowest course ID,
     e.g. 101 Beginner Piano rather than 103 Intermediate Piano),
  3. only then creates the student and enrols them.

  If no teacher teaches that instrument, nothing is created and the form shows an
  error. If a teacher exists but no course has been set up yet, a
  "Beginner <Instrument>" course is opened with that teacher.
- After a successful registration the page reloads with a success message, so
  the new student shows up in the search table straight away.

**Fragment 4.3: Daily Roster & Check-in (`gui/roster_pages.py`)**
- **Daily Roster**: choose a day (it opens on today's weekday) to see that day's
  lessons sorted by time, with course, instrument, teacher, room and class size,
  plus "lessons today" and "students expected" totals.
- **Student Check-in**: choose a student, then one of *their* courses, then press
  **Check-in Student**, which calls `manager.check_in(student_id, course_id)`.
  A checkbox widens the list to every course for trial or drop-in lessons. The
  check-in is still recorded, and the page warns that the student is not
  enrolled.
- **Today's Check-ins**: a live log of every check-in made today, newest first,
  so the receptionist can see the check-in was saved.

### How to Run
```bash
pip install -r requirements.txt     # or: pip install streamlit pandas
streamlit run main.py
```
Run it from the project root. Streamlit opens the app in your browser at
`http://localhost:8501`. Stop it with `Ctrl+C` in the terminal.

### How to Test
The GUI was tested by hand in the browser and with Streamlit's built-in test
tool (`streamlit.testing.v1.AppTest`), which runs the app without a browser,
fills in widgets and presses buttons. After each action, `data/msms.json` was
checked.

| Test | Steps | Expected result |
| --- | --- | --- |
| Search by name | Type `ali` | Only Alice Johnson listed |
| Search by ID | Type `2` | Only Bob Williams listed |
| No match | Type `zzz` | "No student matches 'zzz'." |
| Register | Name `Carol Tan`, instrument ` piano ` | Success message, balloons; Carol (ID 3) appears in the table, enrolled in Beginner Piano; sidebar shows 3 students |
| Unknown instrument | Instrument `Drums` | Error; `msms.json` unchanged (no half-created student) |
| Blank field | Leave name empty | "Please enter both a name and an instrument." |
| Roster | Pick Monday | Beginner Piano, 16:00, Room A, Dr. Evelyn Keys |
| Empty day | Pick Sunday | "No lessons scheduled for Sunday." |
| Check-in | Carol → Beginner Piano | Success; new row in Today's Check-ins and in `attendance` in the JSON |
| Drop-in check-in | Tick the checkbox, Carol → Acoustic Guitar | Success plus a "not enrolled, recorded as a drop-in" warning |
| Persistence | Close the browser tab, run the app again | Carol and her check-ins are still there |

### Design Choices & Assumptions
- **The GUI contains no business logic.** Rules such as "a student needs a
  teacher for their instrument" live in `ScheduleManager`. The pages only check
  that the boxes are not empty, then call a manager method. This is why the
  console in PST3 could be swapped for a GUI without touching the models.
- **One manager per browser session**, kept in `st.session_state`. This follows
  PST3's "one `ScheduleManager` for the whole program" rule. Each change is still
  saved to `data/msms.json` straight away, so nothing is lost if the tab closes.
- **Registration validates before it changes anything**, like `switch_course`
  in PST3. A failed registration never leaves a student with no course.
- **Dropdowns show names but hold objects/IDs.** The template mapped
  `{name: id}`, which would silently merge two students with the same name.
  The dropdowns hold the objects themselves and display `"Name (ID n)"`.
- **The check-in section is not an `st.form`.** Widgets inside a form do not
  refresh until it is submitted, so the course list could not react to the
  chosen student. Using plain widgets lets the course list show only that
  student's courses, which stops most mistaken check-ins before they happen.
- **Drop-ins are allowed but flagged.** PST3's `check_in` records a check-in for
  a student who is not enrolled (for example a trial lesson), but warns. The
  GUI keeps that behaviour and shows the warning on screen instead of only in
  the terminal.
- **The roster offers all seven days** (the template stopped at Friday). Music
  schools often teach at weekends, and an empty day simply shows a message.
- **The text console was retired**, as the brief asks that `main.py` only launch
  the GUI. The PST3 console is still in the Git history (commit `8dfa507`).
- **Payments** remains a stub page; it is scheduled for PST5.



## PST5: The Quality & Finance Gate

### Overview
PST5 solves the "Fragile & Unverified" problem. Up to PST4 the app worked, but
nothing proved it, nothing recorded what happened, there was no safety copy of
the data, and the Payments page was a stub. PST5 adds:

1. **A finance engine** - record payments, view a student's payment history,
   and export the finance or attendance log to CSV (Fragment 5.1).
2. **A real Payments page** in the GUI (Fragment 5.2).
3. **Admin utilities** - an event log (`msms.log`) and timestamped backups of
   `data/msms.json` (Fragment 5.3), wired into the app's start-up and key
   business methods (Fragment 5.4).
4. **An automated test suite** - 38 `pytest` tests (Fragment 5.5).
5. **Crash-proofing** throughout (see the table at the end).

| Layer | Files | Change in PST5 |
| --- | --- | --- |
| **Model** | `app/user.py`, `app/student.py`, `app/teacher.py` | None |
| **Controller** | `app/schedule.py` | `finance_log`; `record_payment`, `get_payment_history`, `get_total_paid`, `export_report`, `cancel_lesson`, `create_course`; logging; crash-safe save |
| **Admin** | `app/admin_utils.py` (new) | `init_logger`, `backup_data`, `list_backups` |
| **View** | `gui/finance_pages.py` (new), `gui/main_dashboard.py`, `gui/roster_pages.py`, `main.py` | Payments page, Backup Now button, page error guard, Cancel a lesson, logging + backup on start-up |
| **Tests** | `tests/` (new), `pytest.ini` | 38 automated tests |

### Project Structure
```
FIT1056-PSTs-36339539/
├── main.py                   # Launcher: logging + backup, then the GUI
├── requirements.txt          # streamlit, pandas, pytest
├── pytest.ini                # NEW: lets a plain "pytest" find app/ and tests/
├── app/
│   ├── user.py, student.py, teacher.py
│   ├── schedule.py           # ScheduleManager (+ finance, reports, cancel_lesson, logging)
│   └── admin_utils.py        # NEW: init_logger, backup_data
├── gui/
│   ├── main_dashboard.py     # Navigation, Backup Now, error guard
│   ├── student_pages.py
│   ├── roster_pages.py       # + Cancel a lesson
│   └── finance_pages.py      # NEW: Finance & Payments page
├── tests/                    # NEW
│   ├── test_schedule_manager.py
│   └── test_admin_utils.py
├── data/
│   ├── msms.json
│   └── backups/              # created at run time (git-ignored)
├── reports/                  # exported CSVs, created at run time (git-ignored)
├── msms.log                  # event log, created at run time (git-ignored)
└── PST2/ ... PST5/           # Brief, rubric and templates for each stage
```

### What Each Part Does

**Fragment 5.1: Finance & Reporting Engine (`app/schedule.py`)**
- `self.finance_log` is a list of payment dictionaries, loaded from and saved
  to a new `"finance"` key in `msms.json`. An older PST4 file with no `"finance"`
  key still loads (as "no payments yet").
- `record_payment(student_id, amount, method)` checks the student exists, the
  amount is a real number above zero (text such as `"abc"`, `0`, negatives,
  NaN and infinity are all refused), and the method is not blank. Only then is a
  record added:
  `{"payment_id": 1, "student_id": 1, "amount": 150.0, "method": "Cash", "timestamp": "2026-10-20T15:44:06"}`.
  It returns the record, or `None` if the payment was rejected.
- `get_payment_history(student_id)` returns that student's payments (a list
  comprehension over the log). `get_total_paid(student_id)` adds them up.
- `export_report(kind, out_path)` writes the `"finance"` or `"attendance"` log to
  a CSV with `csv.DictWriter`. It creates the output folder if needed and
  returns the number of rows written. It returns `None` for an unknown report
  type, or if the file cannot be written (for example, the CSV is open in Excel).

**Fragment 5.2: Finance GUI (`gui/finance_pages.py`)**
`show_finance_page(manager)` replaces the PST4 stub and has four sections:
- **Record New Payment**: a form with a student dropdown, amount in RM, and a
  payment-method dropdown (Cash, Credit Card, Debit Card, Bank Transfer,
  E-wallet, or Other with a text box).
- **View Student Payment History**: pick a student to see their payments, the
  number of payments and the total paid.
- **All Payments**: every payment, newest first, with total takings and
  today's takings.
- **Export Reports**: save the finance or attendance log as a CSV in `reports/`,
  then download it from the page.

**Fragment 5.3: Admin Utilities (`app/admin_utils.py`)**
- `init_logger(log_file)` attaches a file handler to Python's root logger, using
  the format `timestamp - LEVEL - message`, in append mode. Calling it twice does
  not add a second handler, which matters because Streamlit re-runs `main.py`
  on every click and would otherwise write each line many times.
- `backup_data(data_path, backup_dir)` copies `msms.json` to
  `data/backups/msms_backup_YYYY-MM-DD_HH-MM-SS.json`. It creates the folder if
  needed and keeps only the newest 20 backups. It never raises: a failed backup
  is logged and returns `None`, so it cannot stop the app from starting.

**Fragment 5.4: Integrating Admin Utilities**
- `main.py` calls `init_logger()` first, then `backup_data()`, then `launch()`.
  The backup is taken **once per browser session** (guarded by
  `st.session_state`), not on every click.
- `app/schedule.py` logs every key business event: `INFO` for registrations,
  payments, check-ins and exports, and `WARNING` for rejected input and lesson
  cancellations. A corrupted data file is logged as `ERROR`.
- `cancel_lesson(lesson_id, reason)` was added, because the brief logs it but
  the class did not have it. It needs a reason, removes the lesson from the
  timetable and logs a warning. The Daily Roster page has a **Cancel a lesson**
  option with a required reason and a confirmation tick-box.
- The sidebar has a **Backup Now** button and shows how many backups exist.

**Fragment 5.5: Automated Test Suite (`tests/`)**
Each test follows **Arrange, Act, Assert** and checks one thing. The fixtures
build each test's own data file in pytest's `tmp_path`, so the tests **never
touch the real `data/msms.json`** and do not affect each other.

| Area | What is tested |
| --- | --- |
| Courses / lessons | create course; unknown teacher refused; cancel lesson; unknown lesson ID; blank reason refused |
| Registration / check-in | enrols on both sides (case-insensitive instrument); unknown instrument leaves no half-created student; blank name; check-in recorded; bad IDs refused |
| Payments | record + history (template test); empty history for a student who never paid; history only returns that student's payments; totals; unknown student; 6 invalid amounts (0, -50, "abc", None, NaN, inf); blank method; numeric string rounded to cents; unique, increasing payment IDs |
| Persistence | payments survive a reload and IDs continue; an old PST4 file loads; a corrupted file does not crash; no `.tmp` file left after a save |
| CSV export | finance columns and values; attendance; empty log writes header only; unknown kind writes nothing |
| Admin utils | backup is an identical, timestamped copy; missing data file returns `None`; two quick backups do not overwrite; pruning keeps the newest N; payments and rejected payments appear in the log; `init_logger` twice does not duplicate lines |

### How to Run
```bash
pip install -r requirements.txt
streamlit run main.py          # or: python main.py
```
Run it from the project root. On start-up you will see `msms.log` created and
a new file in `data/backups/`.

### How to Test
```bash
pytest
```
`pytest.ini` points pytest at `tests/` and puts the project root on the
import path, so no other set-up is needed. Expected output: **38 passed**.

The GUI was also checked by hand and with Streamlit's `AppTest`. Results:
recording a RM 150 payment updated the history, totals and `msms.json`;
choosing "Other" with no text showed a warning; exporting created a CSV in
`reports/`; Backup Now added a backup; cancelling Monday's lesson removed it
from the roster and wrote a `WARNING` line with the reason to `msms.log`; many
clicks produced only one start-up backup.

### Design Choices & Assumptions
- **Validate before mutate (again).** `record_payment` follows the same rule as
  `register_new_student` and `switch_course`: every check runs before the log
  changes, so a bad payment never reaches the file. The GUI checks too
  (`min_value=0.01`), but the manager does not trust the GUI, which is why the
  tests can call it with bad input directly.
- **Payments get a `payment_id`.** The template record had no ID, so two equal
  payments on the same day could not be told apart, for example on a receipt.
  The counter is saved like the other `next_*_id` counters.
- **Money is stored rounded to 2 decimal places**, so floating-point noise
  (`0.1 + 0.2 = 0.30000000000000004`) never appears. The currency is RM.
- **Payments are kept when a student is removed**, like attendance records.
  Financial history should not disappear, so the GUI shows "Student #n (removed)".
- **`export_report` uses a lookup table** (`REPORT_KINDS`) instead of a long
  if/elif, so a new report type is a one-line change.
- **Cancelling a lesson removes it from the timetable.** The assumption is that
  "cancel" means the timeslot is no longer running. The reason is kept in the
  log as the audit trail.
- **`create_course`** is a thin alias for `add_course`, because the template test
  uses that name. Unlike the template, the test adds a teacher first, since a
  course for a teacher who does not exist is correctly refused.

**Crash-proofing summary**

| Risk | Protection |
| --- | --- |
| App killed while saving | `_save_data` writes `msms.json.tmp` then `os.replace`s it, so `msms.json` is never half-written |
| Corrupted / missing data file | Starts with a clean state and logs an error instead of crashing |
| Older data file (PST4) | Missing keys default via `.get()` |
| Bad payment input | Rejected with a message; never stored |
| Report file locked or folder missing | Folder created; write errors caught and shown in the GUI |
| Backup fails | Logged, returns `None`; the app still starts |
| Unexpected error on any page | Caught in `main_dashboard.py`, full traceback written to `msms.log`, friendly message shown; Streamlit's own rerun signal is let through |
| Backup folder filling up | Only the newest 20 backups are kept |
