from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from gbot.config import WEEKDAYS_RU
from gbot.database.models import Booking, Master, Service
from gbot.keyboards.callbacks import (
    AdminMasterCB,
    AdminServiceCB,
    AdminDayToggleCB,
    AdminDayDoneCB,
    AdminCancelBookingCB,
)


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="👨‍🔧 Мастера")
    builder.button(text="🛠 Услуги")
    builder.button(text="📆 Записи на дату")
    builder.button(text="📢 Рассылка")
    builder.button(text="⬅️ Выйти из админки")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def admin_masters_list_kb(masters: list[Master]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in masters:
        status = "🟢" if m.is_active else "🔴"
        builder.button(
            text=f"{status} {m.name}",
            callback_data=AdminMasterCB(id=m.id, action="view"),
        )
    builder.button(text="➕ Добавить мастера", callback_data="add_master")
    builder.adjust(1)
    return builder.as_markup()


def admin_master_card_kb(master: Master) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "🔴 Деактивировать" if master.is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=AdminMasterCB(id=master.id, action="toggle"))
    builder.button(text="🗑 Удалить", callback_data=AdminMasterCB(id=master.id, action="delete"))
    builder.adjust(1)
    return builder.as_markup()


def admin_services_list_kb(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in services:
        builder.button(
            text=f"{s.name} — {s.price}₽ / {s.duration_minutes} мин",
            callback_data=AdminServiceCB(id=s.id, action="view"),
        )
    builder.button(text="➕ Добавить услугу", callback_data="add_service")
    builder.adjust(1)
    return builder.as_markup()


def admin_service_card_kb(service: Service) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=AdminServiceCB(id=service.id, action="delete"))
    return builder.as_markup()


def admin_days_toggle_kb(selected_days: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, name in enumerate(WEEKDAYS_RU):
        mark = "✅ " if i in selected_days else ""
        builder.button(text=f"{mark}{name}", callback_data=AdminDayToggleCB(day=i))
    builder.button(text="Готово ➡️", callback_data=AdminDayDoneCB())
    builder.adjust(4, 3, 1)
    return builder.as_markup()


def admin_bookings_list_kb(bookings: list[Booking]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        builder.button(
            text=f"❌ {b.time} {b.master.name} — {b.user.full_name}",
            callback_data=AdminCancelBookingCB(id=b.id),
        )
    builder.adjust(1)
    return builder.as_markup()
