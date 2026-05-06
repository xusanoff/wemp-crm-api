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
    created_by   = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    # Student o'chirilsa => barcha bog'liq yozuvlar ham o'chadi
    enrollments  = db.relationship("Enrollment",  backref="student_ref",  lazy="dynamic",
                                    cascade="all, delete-orphan")
    payments     = db.relationship("Payment",     backref="student_ref",  lazy="dynamic",
                                    cascade="all, delete-orphan")
    debts        = db.relationship("Debt",        backref="student_ref",  lazy="dynamic",
                                    cascade="all, delete-orphan")
    monthly_debts= db.relationship("MonthlyDebt", backref="student_ref",  lazy="dynamic",
                                    cascade="all, delete-orphan")
    attendances  = db.relationship("Attendance",  backref="student_ref",  lazy="dynamic",
                                    cascade="all, delete-orphan")
    groups       = db.relationship("Group",       backref="student_ref",  lazy="dynamic",
                                    cascade="all, delete-orphan",
                                    foreign_keys="Group.student_id")

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
