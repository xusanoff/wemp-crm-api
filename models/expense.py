import pytz
from models import db
from datetime import datetime

time_zone = pytz.timezone("Asia/Tashkent")


class Expense(db.Model):
    __tablename__ = "expenses"

    id           = db.Column(db.Integer, primary_key=True)
    amount       = db.Column(db.Float, nullable=False)
    description  = db.Column(db.String(255), nullable=False)
    category     = db.Column(db.String(50), nullable=True)
    expense_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(time_zone).date())
    created_by   = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(time_zone))

    creator = db.relationship("User", backref="expenses", lazy="joined")

    def __init__(self, amount, description, category, expense_date, created_by):
        super().__init__()
        self.amount       = amount
        self.description  = description
        self.category     = category
        self.expense_date = expense_date
        self.created_by   = created_by

    @staticmethod
    def to_dict(expense):
        _ = {
            "id":           expense.id,
            "amount":       expense.amount,
            "description":  expense.description,
            "category":     expense.category,
            "expense_date": str(expense.expense_date),
            "created_by":   expense.created_by,
            "creator_name": expense.creator.full_name if expense.creator else None,
            "created_at":   str(expense.created_at),
        }
        return _
