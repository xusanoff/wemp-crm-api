"""
APScheduler — har kuni soat 20:00 da FAQAT kelmagan o'quvchilar xabari.
"Keldi" deb belgilanganlar darhol (hooks.py orqali) yuborilib bo'ladi,
shuning uchun bu yerda faqat "kelmadi" va "belgilanmagan"lar ko'rsatiladi.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron         import CronTrigger
import pytz

from bot.config     import DAILY_REPORT_HOUR, DAILY_REPORT_MINUTE, TIMEZONE
from bot.api_client import get_today_attendance
from bot.sender     import send_message, daily_absent_message


def send_daily_absent_report():
    """Har kuni soat 20:00 da chaqiriladi — faqat kelmaganlar."""
    try:
        records = get_today_attendance()
        if not records:
            # Bugun dars yo'q — xabar yubormaymiz
            return

        # Faqat kelmadi yoki belgilanmagan o'quvchilar bor bo'lsa xabar yuboramiz
        absent = [r for r in records if r.get("status") != "keldi"]
        msg    = daily_absent_message(records)   # funktsiya ichida o'zi filtrlaydi
        send_message(msg)
        print(f"[BOT] Daily absent report sent: {len(absent)} absent / {len(records)} total")

    except Exception as e:
        print(f"[BOT] Daily absent report error: {e}")


def start_scheduler():
    """Schedulerni ishga tushiradi — app.py dan chaqiriladi."""
    tz        = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    scheduler.add_job(
        func             = send_daily_absent_report,
        trigger          = CronTrigger(
            hour     = DAILY_REPORT_HOUR,
            minute   = DAILY_REPORT_MINUTE,
            timezone = tz,
        ),
        id               = "daily_absent_report",
        replace_existing = True,
        name             = "Kunlik kelmaganlar hisoboti (20:00)",
    )

    scheduler.start()
    print(f"[BOT] Scheduler started — absent report at {DAILY_REPORT_HOUR:02d}:{DAILY_REPORT_MINUTE:02d} {TIMEZONE}")
    return scheduler
