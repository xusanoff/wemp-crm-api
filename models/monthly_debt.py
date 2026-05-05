"""
Har o'quvchi uchun har oylik qarz alohida saqlanadi.
Kurs 3 oy, narx 3600000 => 1200000 / oy
"""
import pytz
from models import db
from datetime import datetime

time_zone = pytz.timezone("Asia/Tashkent")


class MonthlyDebt(db.Model):
    __tablename__ = "monthly_debts"

    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey("students.id"),    nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False)
    for_month     = db.Column(db.String(7), nullable=False)  # "2025-01"
    amount        = db.Column(db.Float, nullable=False)       # oylik summa (kurs_narxi / davomiylik)
    paid_amount   = db.Column(db.Float, default=0.0)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    student    = db.relationship("Student",    backref="monthly_debts", lazy="joined")
    enrollment = db.relationship("Enrollment", backref="monthly_debts", lazy="joined")

    def __init__(self, student_id, enrollment_id, for_month, amount):
        super().__init__()
        self.student_id    = student_id
        self.enrollment_id = enrollment_id
        self.for_month     = for_month
        self.amount        = amount
        self.paid_amount   = 0.0

    @property
    def remaining(self):
        return max(0.0, self.amount - self.paid_amount)

    @property
    def is_paid(self):
        return self.paid_amount >= self.amount

    @staticmethod
    def to_dict(md):
        return {
            "id":            md.id,
            "student_id":    md.student_id,
            "enrollment_id": md.enrollment_id,
            "for_month":     md.for_month,
            "amount":        md.amount,
            "paid_amount":   md.paid_amount,
            "remaining":     md.remaining,
            "is_paid":       md.is_paid,
        }
