import datetime as dt

from aiogram.types import (
    KeyboardButton,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from gbot.database.models import Master, Service, Booking
from gbot.keyboards.callbacks import (
    MasterCB,
    ServiceCB,
    NoServiceCB,
    DateCB,
    TimeCB,
    ConfirmBookingCB,
    CancelBookingCB,
)
from gbot.utils.slots import get_upcoming_dates, format_date_short, format_date_ru


def phone_request_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Отправить номер телефона", request_contact=True))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📅 Записаться")
    builder.button(text="🗂 Мои записи")
    builder.button(text="ℹ️ О нас")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def masters_kb(masters: list[Master]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in masters:
        builder.button(text=m.name, callback_data=MasterCB(id=m.id))
    builder.adjust(1)
    return builder.as_markup()


def services_kb(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in services:
        label = f"{s.name} — {s.price}₽" if s.price else s.name
        builder.button(text=label, callback_data=ServiceCB(id=s.id))
    builder.button(text="Без выбора услуги ➡️", callback_data=NoServiceCB())
    builder.adjust(1)
    return builder.as_markup()


def dates_kb(days_ahead: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in get_upcoming_dates(days_ahead):
        builder.button(text=format_date_short(d), callback_data=DateCB(iso=d.isoformat()))
    builder.adjust(3)
    return builder.as_markup()


def times_kb(slots: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in slots:
        builder.button(text=t, callback_data=TimeCB(value=t))
    builder.adjust(4)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=ConfirmBookingCB(action="yes"))
    builder.button(text="❌ Отменить", callback_data=ConfirmBookingCB(action="no"))
    builder.adjust(2)
    return builder.as_markup()


def my_bookings_kb(bookings: list[Booking]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        builder.button(
            text=f"❌ Отменить {format_date_ru(b.date)} в {b.time}",
            callback_data=CancelBookingCB(id=b.id),
        )
    builder.adjust(1)
    return builder.as_markup()
