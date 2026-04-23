"""
CRM API bilan bog'laning — token olish va ma'lumotlarni yuklash.
"""
import requests
from bot.config import API_BASE, API_USER, API_PASS

_token = None


def get_token():
    """Login qilib JWT token olib qaytaradi."""
    global _token
    r = requests.post(f"{API_BASE}/auth/login", json={
        "username": API_USER,
        "password": API_PASS,
    }, timeout=10)
    if r.ok:
        _token = r.json()["result"]["access_token"]
        return _token
    raise Exception(f"Login failed: {r.text}")


def headers():
    if not _token:
        get_token()
    return {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}


def api_get(path):
    """GET so'rov, token eskirgan bo'lsa qayta login qiladi."""
    global _token
    try:
        r = requests.get(f"{API_BASE}{path}", headers=headers(), timeout=15)
        if r.status_code == 401:
            get_token()  # qayta token
            r = requests.get(f"{API_BASE}{path}", headers=headers(), timeout=15)
        return r.json().get("result")
    except Exception as e:
        print(f"API Error [{path}]: {e}")
        return None


def get_today_attendance():
    """Bugungi barcha davomat yozuvlari."""
    from datetime import date
    today = date.today().isoformat()

    # Barcha o'quvchilarni olamiz
    students = api_get("/operator/students") or []
    result   = []

    for s in students:
        if s.get("enrollment_status") != "active":
            continue

        group_id = s.get("group_id")
        if not group_id:
            continue

        # Bugungi dars
        lessons = api_get(f"/manager/students/{s['id']}/lessons") or []
        today_lesson = next(
            (l for l in lessons if l.get("lesson_date") == today and not l.get("is_cancelled")),
            None
        )
        if not today_lesson:
            continue  # Bugun dars yo'q

        # Davomat
        att_data = api_get(f"/manager/attendance?lesson_id={today_lesson['id']}") or []
        att = next((a for a in att_data if a.get("student_id") == s["id"]), None)

        result.append({
            "student_id":   s["id"],
            "full_name":    s["full_name"],
            "teacher_name": s.get("teacher_name", "—"),
            "course_name":  s.get("course_name", "—"),
            "lesson_id":    today_lesson["id"],
            "lesson_time":  today_lesson.get("lesson_time", "")[:5],
            "status":       att["status"]       if att else None,
            "arrival_time": att.get("arrival_time") if att else None,
        })

    return result