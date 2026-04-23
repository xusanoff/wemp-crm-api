import requests
from bot.config import BOT_TOKEN, CHAT_ID


def send_message(text: str, parse_mode: str = "HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}, timeout=10)
        if not r.ok:
            print(f"Telegram error: {r.text}")
        return r.ok
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


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
        status_icon = "✅"
        status_text = "KELDI"
        arrival_line = f"\n⏰ <b>Kelgan vaqt:</b> {arrival_time}" if arrival_time else ""
    else:
        status_icon = "❌"
        status_text = "KELMADI"
        arrival_line = ""

    # Dars turi emoji
    type_icons = {"dars": "📖", "savol-javob": "❓", "project": "🛠"}
    type_icon  = type_icons.get(lesson_type, "📖")

    # Modul va dars qatori (agar tanlangan bo'lsa)
    module_line  = f"\n📂 <b>Modul:</b> {module_title}" if module_title else ""
    ml_line      = f"\n📝 <b>Dars:</b> {ml_title}" if ml_title else ""
    type_line    = f"\n{type_icon} <b>Tur:</b> {lesson_type.capitalize()}"

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


def daily_report_message(records: list) -> str:
    from datetime import date
    today    = date.today().strftime("%d.%m.%Y")
    weekdays = ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"]
    day_name = weekdays[date.today().weekday()]

    keldi    = [r for r in records if r.get("status") == "keldi"]
    kelmadi  = [r for r in records if r.get("status") == "kelmadi"]
    belgilanmagan = [r for r in records if r.get("status") is None]

    lines = [
        f"📊 <b>KUNLIK DAVOMAT HISOBOTI</b>",
        f"📅 {day_name}, {today}",
        f"━━━━━━━━━━━━━━━━━━",
        f"👥 <b>Jami dars bor:</b> {len(records)} ta",
        f"✅ <b>Keldi:</b> {len(keldi)} ta",
        f"❌ <b>Kelmadi:</b> {len(kelmadi)} ta",
    ]
    if belgilanmagan:
        lines.append(f"⚠️ <b>Belgilanmagan:</b> {len(belgilanmagan)} ta")
    if kelmadi:
        lines.append(f"\n❌ <b>KELMAGANLAR:</b>")
        for i, r in enumerate(kelmadi, 1):
            lines.append(f"  {i}. {r['full_name']} — {r['course_name']} ({r['teacher_name']})")
    if belgilanmagan:
        lines.append(f"\n⚠️ <b>BELGILANMAGANLAR:</b>")
        for i, r in enumerate(belgilanmagan, 1):
            lines.append(f"  {i}. {r['full_name']} — {r['course_name']}")
    lines.append("━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)