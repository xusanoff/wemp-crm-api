"""
Kurs modullari va modul darslar tizimi.

Course → CourseModule (Modul 1, Modul 2...) → ModuleLesson (Dars 1, Dars 2...)
Har bir darsga nom va fayl (PDF/rasm) yuklash mumkin.
"""
import os
import pytz
from models import db
from datetime import datetime

time_zone = pytz.timezone("Asia/Tashkent")


class CourseModule(db.Model):
    """Kursning bir moduli."""
    __tablename__ = "course_modules"

    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title       = db.Column(db.String(200), nullable=False)   # "1-Modul: Kirish"
    order_num   = db.Column(db.Integer, default=1)            # tartib raqami
    description = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    course  = db.relationship("Course", backref="modules", lazy="joined")
    lessons = db.relationship("ModuleLesson", backref="module",
                              lazy="dynamic", cascade="all, delete-orphan",
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
            "id":          m.id,
            "course_id":   m.course_id,
            "course_name": m.course.name if m.course else None,
            "title":       m.title,
            "order_num":   m.order_num,
            "description": m.description,
            "lesson_count": m.lessons.count(),
            "created_at":  str(m.created_at),
        }
        if include_lessons:
            _["lessons"] = [ModuleLesson.to_dict(l) for l in m.lessons]
        return _


class ModuleLesson(db.Model):
    """Modulning bir darsi — nom, tur va fayl bilan."""
    __tablename__ = "module_lessons"

    id          = db.Column(db.Integer, primary_key=True)
    module_id   = db.Column(db.Integer, db.ForeignKey("course_modules.id"), nullable=False)
    title       = db.Column(db.String(200), nullable=False)   # "1-dars: O'zgaruvchilar"
    order_num   = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    # Fayl — PDF yoki rasm
    file_path   = db.Column(db.String(500), nullable=True)    # serverda saqlangan yo'l
    file_name   = db.Column(db.String(200), nullable=True)    # original fayl nomi
    file_type   = db.Column(db.String(50),  nullable=True)    # "pdf" | "image"
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    def __init__(self, module_id, title, order_num=1, description=None):
        super().__init__()
        self.module_id   = module_id
        self.title       = title
        self.order_num   = order_num
        self.description = description

    @staticmethod
    def to_dict(l):
        _ = {
            "id":          l.id,
            "module_id":   l.module_id,
            "title":       l.title,
            "order_num":   l.order_num,
            "description": l.description,
            "file_path":   l.file_path,
            "file_name":   l.file_name,
            "file_type":   l.file_type,
            "has_file":    l.file_path is not None,
            "created_at":  str(l.created_at),
        }
        return _