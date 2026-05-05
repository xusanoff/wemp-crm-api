from models import db


class Group(db.Model):
    """
    Har bir o'quvchi uchun alohida guruh yaratiladi (yakka ta'lim).
    Foydalanuvchiga ko'rinmaydi — orqada avtomatik ishlaydi.
    """
    __tablename__ = "groups"

    id          = db.Column(db.Integer, primary_key=True)
    # Guruh nomi avtomatik: "StudentIsmi - KursNomi"
    name        = db.Column(db.String(150), nullable=False)
    course_id  = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)     # O'qituvchi (User)
    lesson_time = db.Column(db.Time, nullable=False)
    start_date  = db.Column(db.Date, nullable=True)

    course  = db.relationship("Course", backref="groups",  lazy="joined")
    teacher = db.relationship("User",   backref="teaching_groups", lazy="joined", foreign_keys=[teacher_id])
    lessons = db.relationship("Lesson", cascade="all, delete-orphan", passive_deletes=True)

    def __init__(self, name, course_id, lesson_time,
                 student_id=None, teacher_id=None, start_date=None):
        super().__init__()
        self.name        = name
        self.course_id   = course_id
        self.student_id  = student_id
        self.teacher_id  = teacher_id
        self.lesson_time = lesson_time
        self.start_date  = start_date

    @property
    def end_date(self):
        from dateutil.relativedelta import relativedelta
        if self.start_date and self.course and self.course.duration_months:
            return self.start_date + relativedelta(months=self.course.duration_months)
        return None

    @property
    def duration_months(self):
        return self.course.duration_months if self.course else None

    @staticmethod
    def to_dict(group):
        _ = {
            "id":              group.id,
            "name":            group.name,
            "course_id":       group.course_id,
            "course_name":     group.course.name if group.course else None,
            "student_id":      group.student_id,
            "teacher_id":      group.teacher_id,
            "teacher_name":    group.teacher.full_name if group.teacher else None,
            "start_date":      str(group.start_date) if group.start_date else None,
            "end_date":        str(group.end_date)   if group.end_date   else None,
            "duration_months": group.duration_months,
            "lesson_time":     str(group.lesson_time),
        }
        return _
