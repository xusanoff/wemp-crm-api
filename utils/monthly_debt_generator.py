"""
O'quvchi kursga yozilganda har oy uchun alohida qarz yaratadi.
Kurs: 3 oy, narx: 3600000 => [2025-01: 1200000, 2025-02: 1200000, 2025-03: 1200000]
"""
from datetime import date
from dateutil.relativedelta import relativedelta
from models import db
from models.monthly_debt import MonthlyDebt


def generate_monthly_debts(student_id, enrollment_id, course, start_date):
    """
    Kurs davomidagi har oy uchun MonthlyDebt yaratadi.
    Qaytaradi: yaratilgan MonthlyDebt ro'yxati
    """
    monthly_amount = course.price  # oylik narx
    duration       = course.duration_months
    debts          = []

    for i in range(duration):
        for_month_date = start_date + relativedelta(months=i)
        for_month      = for_month_date.strftime("%Y-%m")

        # Avvaldan mavjud bo'lsa, qayta yaratmaslik
        existing = MonthlyDebt.query.filter_by(
            enrollment_id = enrollment_id,
            for_month     = for_month,
        ).first()
        if existing:
            debts.append(existing)
            continue

        md = MonthlyDebt(
            student_id    = student_id,
            enrollment_id = enrollment_id,
            for_month     = for_month,
            amount        = monthly_amount,
        )
        db.session.add(md)
        debts.append(md)

    db.session.flush()
    return debts


def current_month_str():
    return date.today().strftime("%Y-%m")


def current_month_number(start_date):
    """
    start_date dan bugunga qadar necha oy o'tganini hisoblaydi.
    Misol: start_date=2025-01-01, today=2025-03-15 => 3-oy
    """
    if not start_date:
        return 1
    today = date.today()
    delta = relativedelta(today, start_date)
    month_num = delta.years * 12 + delta.months + 1  # 1-oy dan boshlab
    return max(1, month_num)