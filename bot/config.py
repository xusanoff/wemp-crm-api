"""
Telegram bot konfiguratsiyasi.
Bu qiymatlarni .env faylda yoki to'g'ridan-to'g'ri shu yerda o'zgartiring.
"""
import os

# ── Telegram ──────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN",  "8458484762:AAGOem4rPMASxuIC8-BJV7E98eHzd8Ji7mg")
CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID",    "1801631662")   # guruh yoki kanal ID

# ── CRM API ───────────────────────────────────────────────────
API_BASE    = os.getenv("CRM_API_BASE",         "wemp-crm-api-qbht.vercel.app/api")
API_USER    = os.getenv("CRM_BOT_USERNAME",     "akbarov504")
API_PASS    = os.getenv("CRM_BOT_PASSWORD",     "12345678")

# ── Jadval ────────────────────────────────────────────────────
DAILY_REPORT_HOUR   = 20   # Har kuni 20:00 da kelmagan o'quvchilar xabari
DAILY_REPORT_MINUTE = 0
TIMEZONE            = "Asia/Tashkent"
