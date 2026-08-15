# --- Full CRUD for Core Data ---
# Note: We are now working with lists of dictionaries, not lists of objects.

def add_teacher(name, speciality):
    """Adds a teacher dictionary to the data store."""
    # TODO: Get the next teacher ID from app_data['next_teacher_id'].
    teacher_id = app_data['next_teacher_id']
    # TODO: Create a new teacher dictionary with 'id', 'name', and 'speciality' keys.
    new_teacher = {"id": teacher_id, "name": name, "speciality": speciality}
    # TODO: Append the new dictionary to the app_data['teachers'] list.
    app_data['teachers'].append(new_teacher)
    # TODO: Increment the 'next_teacher_id' in app_data.
    app_data['next_teacher_id'] += 1
    print(f"Core: Teacher '{name}' added.")

def update_teacher(teacher_id, **fields):
    """Finds a teacher by ID and updates their data with provided fields."""
    # TODO: Loop through the app_data['teachers'] list.
    for teacher in app_data['teachers']:
        # TODO: If a teacher's 'id' matches teacher_id:
        if teacher['id'] == teacher_id:
            # Use the .update() method on the teacher dictionary to apply the 'fields'.
            teacher.update(fields)
            print(f"Teacher {teacher_id} updated.")
            return
    print(f"Error: Teacher with ID {teacher_id} not found.")

def remove_student(student_id):
    """Removes a student from the data store."""
    
    # Filter the students list to keep everyone EXCEPT the one with the matching ID
    app_data['students'] = [s for s in app_data['students'] if s['id'] != student_id]
    
    print(f"Student {student_id} removed.")


def remove_teacher(teacher_id):
    """Removes a teacher from the data store."""
    
    # Filter the teachers list to keep everyone EXCEPT the one with the matching ID
    app_data['teachers'] = [t for t in app_data['teachers'] if t['id'] != teacher_id]
    
    print(f"Teacher {teacher_id} removed.")


def update_student(student_id, **fields):
    """Finds a student by ID and updates their data with provided fields."""
    
    # Look through the students list to find the specific student we want to update
    for student in app_data['students']:
        
        # Once we find the match, apply the new details and stop searching
        if student['id'] == student_id:
            student.update(fields)
            print(f"Student {student_id} updated.")
            return
            
    # If the loop finishes and we didn't return, the student doesn't exist
    print(f"Error: Student with ID {student_id} not found.")

