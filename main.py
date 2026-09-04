# main.py - The View layer (Fragment 3.4).
#
# This file is only responsible for talking to the user: printing menus, reading
# input, and formatting results. It holds no data and contains no business
# logic - every real operation is delegated to the single ScheduleManager
# object created in main().

from app.schedule import ScheduleManager


# ----------------------------------------------------------------------
# Input helpers - keep the menu from crashing when the user mistypes
# ----------------------------------------------------------------------

def ask_int(prompt):
    """Asks for a whole number. Returns None if the user types something else."""
    raw = input(prompt).strip()
    try:
        return int(raw)
    except ValueError:
        print("Error: that is not a valid number.")
        return None


def ask_text(prompt):
    """Asks for text and strips the surrounding spaces."""
    return input(prompt).strip()


# ----------------------------------------------------------------------
# View functions - each one asks the manager for data, then prints it
# ----------------------------------------------------------------------

def front_desk_daily_roster(manager, day):
    """Displays a table of all lessons on a given day."""
    print(f"\n--- Daily Roster for {day} ---")
    lessons = manager.get_lessons_for_day(day)

    if not lessons:
        print("No lessons scheduled for this day.")
        return

    # Header row, then one line per lesson.
    print(f"{'Time':<8}{'Course':<32}{'Teacher':<22}{'Room':<10}{'Students':<9}")
    print("-" * 81)
    for course, lesson in lessons:
        teacher = manager.find_teacher_by_id(course.teacher_id)
        teacher_name = teacher.name if teacher else "UNASSIGNED"
        print(f"{lesson.get('start_time', '--:--'):<8}"
              f"{course.name:<32}"
              f"{teacher_name:<22}"
              f"{lesson.get('room', '-'):<10}"
              f"{len(course.enrolled_student_ids):<9}")


def list_students(manager):
    """Prints every student and the courses they are enrolled in."""
    print("\n--- All Students ---")
    if not manager.students:
        print("No students on file.")
        return
    for student in manager.students:
        courses = manager.get_courses_for_student(student.id)
        course_names = ", ".join(c.name for c in courses) if courses else "none"
        print(f"  [{student.id}] {student.name}  ->  {course_names}")


def list_teachers(manager):
    """Prints every teacher, their speciality, and the courses they teach."""
    print("\n--- All Teachers ---")
    if not manager.teachers:
        print("No teachers on file.")
        return
    for teacher in manager.teachers:
        taught = [c.name for c in manager.courses if c.teacher_id == teacher.id]
        taught_names = ", ".join(taught) if taught else "none"
        print(f"  [{teacher.id}] {teacher.name} ({teacher.speciality})  ->  {taught_names}")


def list_courses(manager):
    """Prints every course with its teacher, class size, and lesson times."""
    print("\n--- All Courses ---")
    if not manager.courses:
        print("No courses on file.")
        return
    for course in manager.courses:
        teacher = manager.find_teacher_by_id(course.teacher_id)
        teacher_name = teacher.name if teacher else "UNASSIGNED"
        print(f"  [{course.id}] {course.name} ({course.instrument}) - {teacher_name}"
              f" - {len(course.enrolled_student_ids)} student(s)")
        for lesson in course.lessons:
            print(f"        {lesson.get('day')} {lesson.get('start_time')} in {lesson.get('room')}")


def switch_course(manager, student_id, from_course_id, to_course_id):
    """Switches a student between two courses by calling the manager."""
    manager.switch_course(student_id, from_course_id, to_course_id)


def print_student_card(manager, student_id):
    """Writes a text-file ID badge for a student.

    Formatting and file output is a View job, so it lives here rather than in
    the manager. The manager is only asked for the data.
    """
    student = manager.find_student_by_id(student_id)
    if not student:
        print(f"Error: Could not print card, student {student_id} not found.")
        return

    courses = manager.get_courses_for_student(student.id)
    course_names = ", ".join(c.name for c in courses) if courses else "None"
    visits = len(manager.get_attendance_for_student(student.id))

    filename = f"{student_id}_card.txt"
    with open(filename, "w") as f:
        f.write("========================\n")
        f.write("  MUSIC SCHOOL ID BADGE\n")
        f.write("========================\n")
        f.write(f"ID: {student.id}\n")
        f.write(f"Name: {student.name}\n")
        f.write(f"Enrolled In: {course_names}\n")
        f.write(f"Check-ins Recorded: {visits}\n")
    print(f"Printed student card to {filename}.")


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------

def print_menu():
    print("\n===== MSMS v3 (Object-Oriented) =====")
    print("--- View ---")
    print(" 1. Daily roster")
    print(" 2. List students")
    print(" 3. List teachers")
    print(" 4. List courses")
    print("--- Students ---")
    print(" 5. Add student")
    print(" 6. Update student name")
    print(" 7. Remove student")
    print("--- Teachers ---")
    print(" 8. Add teacher")
    print(" 9. Update teacher")
    print("10. Remove teacher")
    print("--- Courses ---")
    print("11. Add course")
    print("12. Update course")
    print("13. Remove course")
    print("14. Add lesson to course")
    print("--- Front desk ---")
    print("15. Enrol student in course")
    print("16. Switch student's course")
    print("17. Check in student")
    print("18. Print student card")
    print(" q. Quit")


def main():
    """Main function to run the MSMS application."""
    # ONE manager for the whole program. Creating it loads the JSON file once;
    # every view function is then handed this same object.
    manager = ScheduleManager()

    while True:
        print_menu()
        choice = input("Enter choice: ").strip().lower()

        if choice == "1":
            day = ask_text("Enter day (e.g., Monday): ")
            front_desk_daily_roster(manager, day)

        elif choice == "2":
            list_students(manager)

        elif choice == "3":
            list_teachers(manager)

        elif choice == "4":
            list_courses(manager)

        elif choice == "5":
            name = ask_text("Student name: ")
            if name:
                manager.add_student(name)
            else:
                print("Error: name cannot be empty.")

        elif choice == "6":
            student_id = ask_int("Student ID: ")
            if student_id is not None:
                name = ask_text("New name: ")
                if name:
                    manager.update_student(student_id, name)
                else:
                    print("Error: name cannot be empty.")

        elif choice == "7":
            student_id = ask_int("Student ID: ")
            if student_id is not None:
                manager.remove_student(student_id)

        elif choice == "8":
            name = ask_text("Teacher name: ")
            speciality = ask_text("Speciality: ")
            if name:
                manager.add_teacher(name, speciality)
            else:
                print("Error: name cannot be empty.")

        elif choice == "9":
            teacher_id = ask_int("Teacher ID: ")
            if teacher_id is not None:
                name = ask_text("New name (leave blank to keep): ")
                speciality = ask_text("New speciality (leave blank to keep): ")
                manager.update_teacher(teacher_id, name, speciality)

        elif choice == "10":
            teacher_id = ask_int("Teacher ID: ")
            if teacher_id is not None:
                manager.remove_teacher(teacher_id)

        elif choice == "11":
            name = ask_text("Course name: ")
            instrument = ask_text("Instrument: ")
            teacher_id = ask_int("Teacher ID: ")
            if name and teacher_id is not None:
                manager.add_course(name, instrument, teacher_id)

        elif choice == "12":
            course_id = ask_int("Course ID: ")
            if course_id is not None:
                name = ask_text("New name (leave blank to keep): ")
                instrument = ask_text("New instrument (leave blank to keep): ")
                raw_teacher = ask_text("New teacher ID (leave blank to keep): ")
                teacher_id = int(raw_teacher) if raw_teacher.isdigit() else None
                manager.update_course(course_id, name, instrument, teacher_id)

        elif choice == "13":
            course_id = ask_int("Course ID: ")
            if course_id is not None:
                manager.remove_course(course_id)

        elif choice == "14":
            course_id = ask_int("Course ID: ")
            if course_id is not None:
                day = ask_text("Day (e.g., Monday): ")
                start_time = ask_text("Start time (e.g., 16:00): ")
                room = ask_text("Room: ")
                manager.add_lesson(course_id, day, start_time, room)

        elif choice == "15":
            student_id = ask_int("Student ID: ")
            course_id = ask_int("Course ID: ") if student_id is not None else None
            if student_id is not None and course_id is not None:
                manager.enrol_student(student_id, course_id)

        elif choice == "16":
            student_id = ask_int("Student ID: ")
            from_course_id = ask_int("Current course ID: ") if student_id is not None else None
            to_course_id = ask_int("New course ID: ") if from_course_id is not None else None
            if student_id is not None and from_course_id is not None and to_course_id is not None:
                switch_course(manager, student_id, from_course_id, to_course_id)

        elif choice == "17":
            student_id = ask_int("Student ID: ")
            course_id = ask_int("Course ID: ") if student_id is not None else None
            if student_id is not None and course_id is not None:
                manager.check_in(student_id, course_id)

        elif choice == "18":
            student_id = ask_int("Student ID: ")
            if student_id is not None:
                print_student_card(manager, student_id)

        elif choice == "q":
            # No final save is needed: the manager saves after every change.
            print("Goodbye.")
            break

        else:
            print("Invalid choice. Please pick a number from the menu, or 'q'.")


if __name__ == "__main__":
    main()
