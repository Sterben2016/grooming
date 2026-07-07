import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()
]

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///grooming.db")

# Render передаёт свой порт через переменную окружения PORT
PORT = int(os.getenv("PORT", 10000))

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS_RU = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]

BOOKING_DAYS_AHEAD = 14  # на сколько дней вперёд можно записаться
