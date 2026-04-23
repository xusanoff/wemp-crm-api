"""
Guruh uchun dars kunlarini avtomatik hisoblash.

Qoida: Dushanbadan Jumagacha (weekday 0-4) — har kuni dars.
Shanba (5) va Yakshanba (6) dam olish kunlari.
"""

from datetime import timedelta
from models import db
from models.lesson import Lesson

# Du=0, Se=1, Cho=2, Pa=3, Ju=4 — ish kunlari
WORK_DAYS = {0, 1, 2, 3, 4}


def generate_lessons_for_group(group) -> int:
    """
    Guruh uchun start_date dan end_date gacha
    Du-Ju kunlari dars yaratadi (mavjud bo'lsa qaytadan qo'shmaydi).
    Qaytaradi: yangi qo'shilgan darslar soni.
    """
    end_date = group.end_date
    if not end_date or not group.start_date:
        return 0

    existing = {
        row.lesson_date
        for row in Lesson.query.filter_by(group_id=group.id).all()
    }

    current_date = group.start_date
    new_count    = 0

    while current_date <= end_date:
        if current_date.weekday() in WORK_DAYS and current_date not in existing:
            lesson = Lesson(
                group_id    = group.id,
                lesson_date = current_date,
                lesson_time = group.lesson_time,
            )
            db.session.add(lesson)
            new_count += 1
        current_date += timedelta(days=1)

    if new_count:
        db.session.commit()

    return new_count