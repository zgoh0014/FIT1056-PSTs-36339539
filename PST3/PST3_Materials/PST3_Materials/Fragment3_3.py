# ... inside the ScheduleManager class ...
import datetime

def check_in(self, student_id, course_id):
    """Records a student's attendance for a course after validation."""
    # This implementation remains the same, but it will now function correctly.
    student = self.find_student_by_id(student_id)
    course = self.find_course_by_id(course_id)
    
    if not student or not course:
        print("Error: Check-in failed. Invalid Student or Course ID.")
        return False
        
    timestamp = datetime.datetime.now().isoformat()
    check_in_record = {"student_id": student_id, "course_id": course_id, "timestamp": timestamp}
    
    # This line will now work without causing an AttributeError.
    self.attendance_log.append(check_in_record)
    self._save_data() # This will now correctly save the attendance log.
    print(f"Success: Student {student.name} checked into {course.name}.")
    return True

# TODO: Also implement find_student_by_id and find_course_by_id helper methods.