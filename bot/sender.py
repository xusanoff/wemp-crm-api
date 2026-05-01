import requests
from bot.config import BOT_TOKEN, CHAT_IDS


def send_message(text: str, parse_mode: str = "HTML"):
    """Barcha CHAT_IDS ga xabar yuboradi."""
    url     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success = True
    for chat_id in CHAT_IDS:
        try:
            r = requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=10
            )
            if not r.ok:
                print(f"Telegram error (chat {chat_id}): {r.text}")
                success = False
        except Exception as e:
            print(f"Telegram send error (chat {chat_id}): {e}")
            success = False
    return success


def attendance_message(record: dict) -> str:
    from datetime import date
    today = date.today().strftime("%d.%m.%Y")

    status       = record.get("status")
    arrival_time = record.get("arrival_time")
    full_name    = record.get("full_name", "—")
    teacher      = record.get("teacher_name", "—")
    course       = record.get("course_name", "—")
    lesson_time  = record.get("lesson_time", "—")
    module_title = record.get("module_title")
    ml_title     = record.get("module_lesson_title")
    lesson_type  = record.get("lesson_type", "dars")

    if status == "keldi":
        status_icon  = "✅"
        arrival_line = f"\n⏰ <b>Kelgan vaqt:</b> {arrival_time}" if arrival_time else ""
    else:
        status_icon  = "❌"
        arrival_line = ""

    type_icons = {"dars": "📖", "savol-javob": "❓", "project": "🛠"}
    type_icon  = type_icons.get(lesson_type, "📖")

    module_line = f"\n📂 <b>Modul:</b> {module_title}" if module_title else ""
    ml_line     = f"\n📝 <b>Dars:</b> {ml_title}"      if ml_title     else ""
    type_line   = f"\n{type_icon} <b>Tur:</b> {lesson_type.capitalize()}"

    return (
        f"{status_icon} <b>DAVOMAT — {today}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>O'quvchi:</b> {full_name}\n"
        f"📚 <b>Kurs:</b> {course}\n"
        f"👨‍🏫 <b>Ustoz:</b> {teacher}\n"
        f"🕐 <b>Dars vaqti:</b> {lesson_time}"
        f"{module_line}{ml_line}{type_line}{arrival_line}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def daily_absent_message(records: list) -> str:
    """Faqat kelmagan o'quvchilar — soat 20:00 da yuboriladigan xabar."""
    from datetime import date
    today    = date.today().strftime("%d.%m.%Y")
    weekdays = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    day_name = weekdays[date.today().weekday()]

    kelmadi       = [r for r in records if r.get("status") == "kelmadi"]
    # status None = bugun dars bor lekin davomat belgilanmagan
    belgilanmagan = [r for r in records if r.get("status") is None]

    if not kelmadi and not belgilanmagan:
        return (
            f"✅ <b>DAVOMAT YAKUNLANDI — {today}</b>\n"
            f"📅 {day_name}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Barcha o'quvchilar keldi! 🎉\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    lines = [
        f"🔔 <b>KELMAGAN O'QUVCHILAR — {today}</b>",
        f"📅 {day_name}",
        f"━━━━━━━━━━━━━━━━━━",
    ]

    if kelmadi:
        lines.append(f"❌ <b>KELMADI ({len(kelmadi)} ta):</b>")
        for i, r in enumerate(kelmadi, 1):
            lines.append(f"  {i}. {r['full_name']} — {r.get('course_name','—')} ({r.get('teacher_name','—')})")

    if belgilanmagan:
        lines.append(f"\n⚠️ <b>BELGILANMAGAN ({len(belgilanmagan)} ta):</b>")
        for i, r in enumerate(belgilanmagan, 1):
            lines.append(f"  {i}. {r['full_name']} — {r.get('course_name','—')}")

    lines.append("━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
