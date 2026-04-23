"""
APScheduler — har kuni soat 20:00 da kelmagan o'quvchilar xabari.
Bu faylni app.py bilan birga ishga tushiramiz.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron         import CronTrigger
import pytz
from bot.config  import DAILY_REPORT_HOUR, DAILY_REPORT_MINUTE, TIMEZONE
from bot.api_client import get_today_attendance
from bot.sender     import send_message, daily_report_message


def send_daily_report():
    """Har kuni soat 20:00 da chaqiriladi."""
    try:
        records = get_today_attendance()
        if not records:
            # Bugun dars yo'q — xabar yubormasa ham bo'ladi
            return
        msg = daily_report_message(records)
        send_message(msg)
        print(f"[BOT] Daily report sent: {len(records)} students")
    except Exception as e:
        print(f"[BOT] Daily report error: {e}")


def start_scheduler():
    """Schedulerni ishga tushiradi — app.py dan chaqiriladi."""
    tz        = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    scheduler.add_job(
        func    = send_daily_report,
        trigger = CronTrigger(
            hour   = DAILY_REPORT_HOUR,
            minute = DAILY_REPORT_MINUTE,
            timezone = tz,
        ),
        id      = "daily_attendance_report",
        replace_existing = True,
        name    = "Kunlik davomat hisoboti",
    )

    scheduler.start()
    print(f"[BOT] Scheduler started — daily report at {DAILY_REPORT_HOUR:02d}:{DAILY_REPORT_MINUTE:02d} {TIMEZONE}")
    return scheduler