"""
Telegram bot konfiguratsiyasi.
Bu qiymatlarni .env faylda yoki to'g'ridan-to'g'ri shu yerda o'zgartiring.
"""
import os

# ── Telegram ──────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8458484762:AAGOem4rPMASxuIC8-BJV7E98eHzd8Ji7mg")

# Bir nechta chat ID — vergul bilan ajrating yoki ro'yxat sifatida
# Misol env: TELEGRAM_CHAT_IDS="1801631662,987654321,112233445"
_chat_ids_env   = os.getenv("TELEGRAM_CHAT_IDS", "1801631662, 1465570653")
_chat_id_single = os.getenv("TELEGRAM_CHAT_ID",  "")

if _chat_ids_env:
    CHAT_IDS = [cid.strip() for cid in _chat_ids_env.split(",") if cid.strip()]
else:
    CHAT_IDS = [_chat_id_single]

# ❗ To'g'ridan-to'g'ri shu yerda ham qo'shsa bo'ladi (env o'rniga):
# CHAT_IDS = [
#     "1801631662",   # 1-admin
#     "987654321",    # 2-admin
#     "112233445",    # 3-admin
# ]

# ── CRM API ───────────────────────────────────────────────────
API_BASE = os.getenv("CRM_API_BASE",      "https://wemp-crm-api-qbht.vercel.app/api")
API_USER = os.getenv("CRM_BOT_USERNAME",  "akbarov504")
API_PASS = os.getenv("CRM_BOT_PASSWORD",  "12345678")

# ── Jadval ────────────────────────────────────────────────────
DAILY_REPORT_HOUR   = 20   # Har kuni 20:00 da kelmagan o'quvchilar xabari
DAILY_REPORT_MINUTE = 0
TIMEZONE            = "Asia/Tashkent"
