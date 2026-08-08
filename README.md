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