"""
Davomat belgilanganida darhol Telegram xabar yuborish.
"""
from bot.sender import send_message, attendance_message
from models.student import Student
from models.group   import Group


def notify_attendance(saved_records: list, lesson_info: dict):
    """
    saved_records ichida:
      student_name, status, arrival_time, module_title, module_lesson_title, lesson_type
    """
    try:
        for rec in saved_records:
            student_id = rec.get("student_id")
            student    = Student.query.filter_by(id=student_id).first()
            if not student:
                continue

            group = Group.query.filter_by(student_id=student_id).first()

            record = {
                "full_name":          rec.get("student_name") or student.full_name,
                "teacher_name":       group.teacher.full_name if group and group.teacher else "—",
                "course_name":        group.course.name       if group and group.course  else "—",
                "lesson_time":        lesson_info.get("lesson_time", "")[:5],
                "status":             rec.get("status"),
                "arrival_time":       rec.get("arrival_time"),
                "module_title":       rec.get("module_title"),
                "module_lesson_title":rec.get("module_lesson_title"),
                "lesson_type":        rec.get("lesson_type", "dars"),
            }

            msg = attendance_message(record)
            send_message(msg)

    except Exception as e:
        print(f"[BOT] notify_attendance error: {e}")