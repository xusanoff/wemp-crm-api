"""
Kurs modullari va modul darslar tizimi.

Course → CourseModule (Modul 1, Modul 2...) → ModuleLesson (Dars 1, Dars 2...)
Har bir darsga nom va fayl (PDF/rasm) yuklash mumkin.
"""
import pytz
from models import db
from datetime import datetime

time_zone = pytz.timezone("Asia/Tashkent")


class CourseModule(db.Model):
    """Kursning bir moduli."""
    __tablename__ = "course_modules"

    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    order_num   = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    # backref ishlatilmaydi — course.py da relationship aniqlangan
    course  = db.relationship("Course", foreign_keys=[course_id], lazy="joined")

    # CourseModule o'chirilsa => ModuleLesson lar ham o'chadi
    lessons = db.relationship("ModuleLesson", backref="module_ref", lazy="dynamic",
                               cascade="all, delete-orphan",
                               order_by="ModuleLesson.order_num")

    def __init__(self, course_id, title, order_num=1, description=None):
        super().__init__()
        self.course_id   = course_id
        self.title       = title
        self.order_num   = order_num
        self.description = description

    @staticmethod
    def to_dict(m, include_lessons=False):
        _ = {
            "id":           m.id,
            "course_id":    m.course_id,
            "course_name":  m.course.name if m.course else None,
            "title":        m.title,
            "order_num":    m.order_num,
            "description":  m.description,
            "lesson_count": m.lessons.count(),
            "created_at":   str(m.created_at),
        }
        if include_lessons:
            _["lessons"] = [ModuleLesson.to_dict(l) for l in m.lessons]
        return _


class ModuleLesson(db.Model):
    """Modulning bir darsi."""
    __tablename__ = "module_lessons"

    id          = db.Column(db.Integer, primary_key=True)
    module_id   = db.Column(db.Integer, db.ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    order_num   = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    file_path   = db.Column(db.String(500), nullable=True)
    file_name   = db.Column(db.String(200), nullable=True)
    file_type   = db.Column(db.String(50),  nullable=True)
    file_data   = db.Column(db.Text,    nullable=True)
    file_size   = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    # backref ishlatilmaydi — course_module.py da relationship aniqlangan
    module = db.relationship("CourseModule", foreign_keys=[module_id], lazy="joined")

    def __init__(self, module_id, title, order_num=1, description=None):
        super().__init__()
        self.module_id   = module_id
        self.title       = title
        self.order_num   = order_num
        self.description = description

    @staticmethod
    def to_dict(l):
        return {
            "id":          l.id,
            "module_id":   l.module_id,
            "title":       l.title,
            "order_num":   l.order_num,
            "description": l.description,
            "file_name":   l.file_name,
            "file_type":   l.file_type,
            "file_size":   l.file_size,
            "has_file":    bool(l.file_data or l.file_path),
            "created_at":  str(l.created_at),
        }
