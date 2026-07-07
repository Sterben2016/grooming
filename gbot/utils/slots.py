import datetime as dt

from gbot.config import MONTHS_RU, WEEKDAYS_RU
from gbot.database.models import Master


def generate_all_slots(master: Master) -> list[str]:
    """Все возможные слоты за рабочий день мастера, шаг = slot_duration."""
    start_h, start_m = map(int, master.work_start.split(":"))
    end_h, end_m = map(int, master.work_end.split(":"))

    start = dt.datetime(2000, 1, 1, start_h, start_m)
    end = dt.datetime(2000, 1, 1, end_h, end_m)

    step = dt.timedelta(minutes=master.slot_duration)

    slots = []
    current = start
    while current + step <= end:
        slots.append(current.strftime("%H:%M"))
        current += step
    return slots


def get_available_slots(master: Master, date: dt.date, booked_times: list[str]) -> list[str]:
    weekday = date.weekday()  # 0 = Пн
    if weekday not in master.work_days_list():
        return []

    all_slots = generate_all_slots(master)
    available = [t for t in all_slots if t not in booked_times]

    if date == dt.date.today():
        now = dt.datetime.now().strftime("%H:%M")
        available = [t for t in available if t > now]

    return available


def get_upcoming_dates(days_ahead: int) -> list[dt.date]:
    today = dt.date.today()
    return [today + dt.timedelta(days=i) for i in range(days_ahead)]


def format_date_ru(date: dt.date) -> str:
    weekday = WEEKDAYS_RU[date.weekday()]
    month = MONTHS_RU[date.month - 1]
    return f"{weekday}, {date.day} {month}"


def format_date_short(date: dt.date) -> str:
    weekday = WEEKDAYS_RU[date.weekday()]
    return f"{weekday} {date.strftime('%d.%m')}"
