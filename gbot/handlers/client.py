import datetime as dt

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from gbot.config import ADMIN_IDS, BOOKING_DAYS_AHEAD
from gbot.database.requests import (
    cancel_booking,
    create_booking,
    get_active_masters,
    get_active_services,
    get_booked_times,
    get_master,
    get_service,
    get_user_active_bookings,
    get_user_by_tg_id,
)
from gbot.keyboards.callbacks import (
    ConfirmBookingCB,
    DateCB,
    MasterCB,
    NoServiceCB,
    ServiceCB,
    TimeCB,
    CancelBookingCB,
)
from gbot.keyboards.client_kb import (
    confirm_kb,
    dates_kb,
    masters_kb,
    my_bookings_kb,
    services_kb,
    times_kb,
)
from gbot.states.states import Booking
from gbot.utils.slots import format_date_ru, get_available_slots

router = Router(name="client")


@router.message(F.text == "📅 Записаться")
async def start_booking(message: Message, state: FSMContext):
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала нажмите /start, чтобы зарегистрироваться.")
        return

    masters = await get_active_masters()
    if not masters:
        await message.answer("Пока нет доступных мастеров. Загляните позже 🙏")
        return

    await state.clear()
    await message.answer("Выберите мастера:", reply_markup=masters_kb(masters))
    await state.set_state(Booking.choosing_master)


@router.callback_query(Booking.choosing_master, MasterCB.filter())
async def choose_master(callback: CallbackQuery, callback_data: MasterCB, state: FSMContext):
    master = await get_master(callback_data.id)
    if not master or not master.is_active:
        await callback.answer("Мастер недоступен", show_alert=True)
        return

    await state.update_data(master_id=master.id, master_name=master.name)

    services = await get_active_services()
    if services:
        await callback.message.edit_text(
            f"Мастер: {master.name}\n\nВыберите услугу:",
        )
        await callback.message.answer("Услуги:", reply_markup=services_kb(services))
        await state.set_state(Booking.choosing_service)
    else:
        await state.update_data(service_id=None, service_name=None)
        await callback.message.edit_text(f"Мастер: {master.name}\n\nВыберите дату:")
        await callback.message.answer("Дата:", reply_markup=dates_kb(BOOKING_DAYS_AHEAD))
        await state.set_state(Booking.choosing_date)

    await callback.answer()


@router.callback_query(Booking.choosing_service, ServiceCB.filter())
async def choose_service(callback: CallbackQuery, callback_data: ServiceCB, state: FSMContext):
    service = await get_service(callback_data.id)
    if not service:
        await callback.answer("Услуга недоступна", show_alert=True)
        return

    await state.update_data(service_id=service.id, service_name=service.name)
    await callback.message.edit_text(f"Услуга: {service.name}\n\nВыберите дату:")
    await callback.message.answer("Дата:", reply_markup=dates_kb(BOOKING_DAYS_AHEAD))
    await state.set_state(Booking.choosing_date)
    await callback.answer()


@router.callback_query(Booking.choosing_service, NoServiceCB.filter())
async def choose_no_service(callback: CallbackQuery, state: FSMContext):
    await state.update_data(service_id=None, service_name=None)
    await callback.message.edit_text("Без конкретной услуги.\n\nВыберите дату:")
    await callback.message.answer("Дата:", reply_markup=dates_kb(BOOKING_DAYS_AHEAD))
    await state.set_state(Booking.choosing_date)
    await callback.answer()


@router.callback_query(Booking.choosing_date, DateCB.filter())
async def choose_date(callback: CallbackQuery, callback_data: DateCB, state: FSMContext):
    date = dt.date.fromisoformat(callback_data.iso)
    data = await state.get_data()

    master = await get_master(data["master_id"])
    booked = await get_booked_times(master.id, date)
    slots = get_available_slots(master, date, booked)

    if not slots:
        await callback.answer("На эту дату нет свободных окошек, выберите другую 🙏", show_alert=True)
        return

    await state.update_data(date_iso=date.isoformat())
    await callback.message.edit_text(f"Дата: {format_date_ru(date)}\n\nВыберите время:")
    await callback.message.answer("Время:", reply_markup=times_kb(slots))
    await state.set_state(Booking.choosing_time)
    await callback.answer()


@router.callback_query(Booking.choosing_time, TimeCB.filter())
async def choose_time(callback: CallbackQuery, callback_data: TimeCB, state: FSMContext):
    await state.update_data(time=callback_data.value)
    data = await state.get_data()

    date = dt.date.fromisoformat(data["date_iso"])
    service_line = f"\nУслуга: {data.get('service_name')}" if data.get("service_name") else ""

    text = (
        "Проверьте данные записи:\n\n"
        f"Мастер: {data['master_name']}{service_line}\n"
        f"Дата: {format_date_ru(date)}\n"
        f"Время: {callback_data.value}\n\n"
        "Подтверждаете запись?"
    )
    await callback.message.edit_text(text)
    await callback.message.answer("Подтвердите:", reply_markup=confirm_kb())
    await state.set_state(Booking.confirming)
    await callback.answer()


@router.callback_query(Booking.confirming, ConfirmBookingCB.filter())
async def confirm_booking(
    callback: CallbackQuery, callback_data: ConfirmBookingCB, state: FSMContext, bot: Bot
):
    if callback_data.action == "no":
        await callback.message.edit_text("Запись отменена. Чтобы начать заново — нажмите «📅 Записаться».")
        await state.clear()
        await callback.answer()
        return

    data = await state.get_data()
    user = await get_user_by_tg_id(callback.from_user.id)
    date = dt.date.fromisoformat(data["date_iso"])

    # финальная проверка, что слот всё ещё свободен
    booked = await get_booked_times(data["master_id"], date)
    if data["time"] in booked:
        await callback.answer("Увы, это время уже заняли. Выберите другое 🙏", show_alert=True)
        await state.clear()
        return

    booking = await create_booking(
        user_id=user.id,
        master_id=data["master_id"],
        service_id=data.get("service_id"),
        date=date,
        time=data["time"],
    )

    service_line = f"\nУслуга: {data.get('service_name')}" if data.get("service_name") else ""
    await callback.message.edit_text(
        "✅ Запись подтверждена!\n\n"
        f"Мастер: {data['master_name']}{service_line}\n"
        f"Дата: {format_date_ru(date)}\n"
        f"Время: {data['time']}\n\n"
        "Ждём вас и вашего питомца! 🐾"
    )
    await state.clear()
    await callback.answer()

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🆕 Новая запись!\n\n"
                f"Клиент: {user.full_name} ({user.phone})\n"
                f"Мастер: {data['master_name']}{service_line}\n"
                f"Дата: {format_date_ru(date)}, время: {data['time']}",
            )
        except Exception:
            pass


@router.message(F.text == "🗂 Мои записи")
async def my_bookings(message: Message):
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала нажмите /start.")
        return

    bookings = await get_user_active_bookings(user.id)
    if not bookings:
        await message.answer("У вас пока нет активных записей.")
        return

    lines = ["Ваши записи:\n"]
    for b in bookings:
        service_line = f", {b.service.name}" if b.service else ""
        lines.append(f"• {format_date_ru(b.date)} в {b.time} — {b.master.name}{service_line}")

    await message.answer("\n".join(lines), reply_markup=my_bookings_kb(bookings))


@router.callback_query(CancelBookingCB.filter())
async def cancel_booking_handler(callback: CallbackQuery, callback_data: CancelBookingCB, bot: Bot):
    await cancel_booking(callback_data.id)
    await callback.message.edit_text("Запись отменена ❌. Будем рады видеть вас в другой раз!")
    await callback.answer()


@router.message(F.text == "ℹ️ О нас")
async def about(message: Message):
    await message.answer(
        "🐾 Наш груминг-салон заботится о красоте и здоровье вашего питомца.\n"
        "Опытные мастера, аккуратный уход и приятная атмосфера.\n\n"
        "Чтобы записаться — нажмите «📅 Записаться»."
    )
