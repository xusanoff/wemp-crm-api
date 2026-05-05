from models import db


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    group_id   = db.Column(db.Integer, db.ForeignKey("groups.id",   ondelete="CASCADE"), nullable=False)
    status     = db.Column(db.String(20), default="active")

    student = db.relationship("Student", backref="enrollments", lazy="joined")
    # group relationship — group.py dagi backref="group" bilan to'qnashmaydi
    group   = db.relationship("Group",   lazy="joined", foreign_keys=[group_id])

    # CASCADE: Enrollment o'chirilsa, debt va monthly_debts ham o'chadi
    debt          = db.relationship("Debt",        backref="enrollment_ref", lazy="joined",
                                    cascade="all, delete-orphan", uselist=False,
                                    foreign_keys="Debt.enrollment_id")
    monthly_debts = db.relationship("MonthlyDebt", backref="enrollment_ref", lazy="dynamic",
                                    cascade="all, delete-orphan",
                                    foreign_keys="MonthlyDebt.enrollment_id")

    def __init__(self, student_id, group_id, status="active"):
        super().__init__()
        self.student_id = student_id
        self.group_id   = group_id
        self.status     = status

    @staticmethod
    def to_dict(enrollment):
        _ = {
            "id":         enrollment.id,
            "student_id": enrollment.student_id,
            "group_id":   enrollment.group_id,
            "status":     enrollment.status,
        }
        return _
