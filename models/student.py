import pytz
from models import db
from datetime import datetime

time_zone = pytz.timezone("Asia/Tashkent")


class Student(db.Model):
    __tablename__ = "students"

    id           = db.Column(db.Integer, primary_key=True)
    full_name    = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), unique=True)
    comment      = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))


    groups = db.relationship("Group", cascade="all, delete-orphan", passive_deletes=True)
    enrollments = db.relationship("Enrollment",back_populates="student",cascade="all, delete-orphan",passive_deletes=True)
    payments = db.relationship("Payment", cascade="all, delete-orphan", passive_deletes=True)
    debts = db.relationship("Debt", cascade="all, delete-orphan", passive_deletes=True)
    monthly_debts = db.relationship("MonthlyDebt", cascade="all, delete-orphan", passive_deletes=True)
    attendance = db.relationship("Attendance", cascade="all, delete-orphan", passive_deletes=True)

    def __init__(self, full_name, phone_number=None, comment=None, created_by=None):
        super().__init__()
        self.full_name    = full_name
        self.phone_number = phone_number
        self.comment      = comment
        self.created_by   = created_by

    @staticmethod
    def to_dict(student):
        _ = {
            "id":           student.id,
            "full_name":    student.full_name,
            "phone_number": student.phone_number,
            "comment":      student.comment,
            "created_by":   student.created_by,
            "created_at":   str(student.created_at),
        }
        return _
