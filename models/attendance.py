from models import db


class Attendance(db.Model):
    __tablename__ = "attendance"

    id               = db.Column(db.Integer, primary_key=True)
    lesson_id        = db.Column(db.Integer, db.ForeignKey("lessons.id",        ondelete="CASCADE"))
    student_id       = db.Column(db.Integer, db.ForeignKey("students.id",       ondelete="CASCADE"))
    status           = db.Column(db.String(10))            # "keldi" | "kelmadi"
    arrival_time     = db.Column(db.String(5), nullable=True)  # "09:15"

    module_id        = db.Column(db.Integer, db.ForeignKey("course_modules.id",  ondelete="SET NULL"), nullable=True)
    module_lesson_id = db.Column(db.Integer, db.ForeignKey("module_lessons.id",  ondelete="SET NULL"), nullable=True)
    lesson_type      = db.Column(db.String(20), default="dars", nullable=True)

    # lesson relationship — lesson.py dagi backref="lesson" bilan to'qnashmaydi
    lesson        = db.relationship("Lesson",       lazy="joined", foreign_keys=[lesson_id])
    module        = db.relationship("CourseModule", lazy="joined", foreign_keys=[module_id])
    module_lesson = db.relationship("ModuleLesson", lazy="joined", foreign_keys=[module_lesson_id])

    def __init__(self, lesson_id, student_id, status, arrival_time=None,
                 module_id=None, module_lesson_id=None, lesson_type="dars"):
        super().__init__()
        self.lesson_id        = lesson_id
        self.student_id       = student_id
        self.status           = status
        self.arrival_time     = arrival_time
        self.module_id        = module_id
        self.module_lesson_id = module_lesson_id
        self.lesson_type      = lesson_type or "dars"

    @staticmethod
    def to_dict(a):
        return {
            "id":               a.id,
            "lesson_id":        a.lesson_id,
            "student_id":       a.student_id,
            "status":           a.status,
            "arrival_time":     a.arrival_time,
            "module_id":        a.module_id,
            "module_title":     a.module.title if a.module else None,
            "module_lesson_id": a.module_lesson_id,
            "module_lesson_title": a.module_lesson.title if a.module_lesson else None,
            "lesson_type":      a.lesson_type,
        }
