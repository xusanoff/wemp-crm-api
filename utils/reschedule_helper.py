"""
Darsni bekor qilish va keyingi bo'sh ish kuniga surish logikasi.
Faqat Du-Ju (weekday 0-4) kunlari suriladi.
"""

from datetime import timedelta
from models import db
from models.lesson import Lesson

WORK_DAYS = {0, 1, 2, 3, 4}


def cancel_and_reschedule(group, cancel_date, reason: str = None):
    lesson = Lesson.query.filter_by(
        group_id     = group.id,
        lesson_date  = cancel_date,
        is_cancelled = False,
    ).first()

    if not lesson:
        return None, f"Guruh #{group.id} uchun {cancel_date} sanasida faol dars topilmadi"

    lesson.is_cancelled  = True
    lesson.cancel_reason = reason

    existing_dates = {
        row.lesson_date
        for row in Lesson.query.filter_by(group_id=group.id).all()
    }

    new_date   = cancel_date + timedelta(days=1)
    end_date   = group.end_date
    warning    = None
    new_lesson = None

    while new_date <= end_date:
        # Faqat Du-Ju kunlari (Shanba, Yakshanba — yo'q)
        if new_date.weekday() not in WORK_DAYS:
            new_date += timedelta(days=1)
            continue

        if new_date not in existing_dates:
            new_lesson = Lesson(
                group_id       = group.id,
                lesson_date    = new_date,
                lesson_time    = group.lesson_time,
                is_rescheduled = True,
                original_date  = cancel_date,
            )
            db.session.add(new_lesson)
            break

        new_date += timedelta(days=1)
    else:
        warning = (
            f"{cancel_date} sanasidagi dars bekor qilindi, lekin "
            f"end_date ({end_date}) dan oldin bo'sh kun topilmadi. "
            f"Dars surilmadi — qo'lda qo'shish tavsiya etiladi."
        )

    db.session.commit()

    return {
        "cancelled_lesson":   Lesson.to_dict(lesson),
        "rescheduled_lesson": Lesson.to_dict(new_lesson) if new_lesson else None,
        "warning":            warning,
    }, None