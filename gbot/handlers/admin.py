import datetime as dt

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from gbot.config import ADMIN_IDS
from gbot.database.requests import (
    create_master,
    create_service,
    delete_master,
    delete_service,
    get_all_masters,
    get_all_services,
    get_all_users,
    get_bookings_for_date,
    get_master,
    get_service,
    toggle_master_active,
    cancel_booking,
)
from gbot.keyboards.admin_kb import (
    admin_bookings_list_kb,
    admin_days_toggle_kb,
    admin_master_card_kb,
    admin_masters_list_kb,
    admin_menu_kb,
    admin_service_card_kb,
    admin_services_list_kb,
)
from gbot.keyboards.callbacks import (
    AdminCancelBookingCB,
    AdminDayDoneCB,
    AdminDayToggleCB,
    AdminMasterCB,
    AdminServiceCB,
)
from gbot.keyboards.client_kb import main_menu_kb
from gbot.states.states import AdminAddMaster, AdminAddService, AdminBookingsByDate, AdminBroadcast
from gbot.utils.slots import format_date_ru

router = Router(name="admin")
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


@router.message(Command("admin"))
async def open_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔧 Панель администратора", reply_markup=admin_menu_kb())


@router.message(F.text == "⬅️ Выйти из админки")
async def exit_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вышли из админ-панели.", reply_markup=main_menu_kb())


# ---------------- MASTERS ----------------

@router.message(F.text == "👨‍🔧 Мастера")
async def masters_list(message: Message):
    masters = await get_all_masters()
    await message.answer(
        "Мастера:" if masters else "Пока нет ни одного мастера.",
        reply_markup=admin_masters_list_kb(masters),
    )


@router.callback_query(F.data == "add_master")
async def add_master_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(selected_days=set())
    await callback.message.answer("Введите имя нового мастера:")
    await state.set_state(AdminAddMaster.waiting_name)
    await callback.answer()


@router.message(AdminAddMaster.waiting_name)
async def add_master_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(
        "Выберите рабочие дни мастера (нажмите на дни, затем «Готово»):",
        reply_markup=admin_days_toggle_kb(set()),
    )
    await state.set_state(AdminAddMaster.waiting_days)


@router.callback_query(AdminAddMaster.waiting_days, AdminDayToggleCB.filter())
async def add_master_toggle_day(
    callback: CallbackQuery, callback_data: AdminDayToggleCB, state: FSMContext
):
    data = await state.get_data()
    selected: set[int] = set(data.get("selected_days", set()))
    if callback_data.day in selected:
        selected.remove(callback_data.day)
    else:
        selected.add(callback_data.day)
    await state.update_data(selected_days=selected)
    await callback.message.edit_reply_markup(reply_markup=admin_days_toggle_kb(selected))
    await callback.answer()


@router.callback_query(AdminAddMaster.waiting_days, AdminDayDoneCB.filter())
async def add_master_days_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected: set[int] = set(data.get("selected_days", set()))
    if not selected:
        await callback.answer("Выберите хотя бы один день", show_alert=True)
        return

    await callback.message.answer("Во сколько мастер начинает работу? Формат ЧЧ:ММ, например 09:00")
    await state.set_state(AdminAddMaster.waiting_start)
    await callback.answer()


def _valid_time(text: str) -> bool:
    try:
        h, m = map(int, text.strip().split(":"))
        return 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        return False


@router.message(AdminAddMaster.waiting_start)
async def add_master_start_time(message: Message, state: FSMContext):
    if not _valid_time(message.text):
        await message.answer("Неверный формат. Введите время как ЧЧ:ММ, например 09:00")
        return
    await state.update_data(work_start=message.text.strip())
    await message.answer("Во сколько мастер заканчивает работу? Формат ЧЧ:ММ, например 18:00")
    await state.set_state(AdminAddMaster.waiting_end)


@router.message(AdminAddMaster.waiting_end)
async def add_master_end_time(message: Message, state: FSMContext):
    if not _valid_time(message.text):
        await message.answer("Неверный формат. Введите время как ЧЧ:ММ, например 18:00")
        return
    await state.update_data(work_end=message.text.strip())
    await message.answer("Длительность одного слота в минутах? Например 60")
    await state.set_state(AdminAddMaster.waiting_duration)


@router.message(AdminAddMaster.waiting_duration)
async def add_master_duration(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Введите число минут, например 60")
        return

    data = await state.get_data()
    selected_days = sorted(data["selected_days"])
    work_days = ",".join(str(d) for d in selected_days)

    master = await create_master(
        name=data["name"],
        work_days=work_days,
        work_start=data["work_start"],
        work_end=data["work_end"],
        slot_duration=int(message.text.strip()),
    )

    await state.clear()
    await message.answer(
        f"✅ Мастер «{master.name}» добавлен!",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(AdminMasterCB.filter(F.action == "view"))
async def master_card(callback: CallbackQuery, callback_data: AdminMasterCB):
    master = await get_master(callback_data.id)
    if not master:
        await callback.answer("Мастер не найден", show_alert=True)
        return

    days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    days_str = ", ".join(days_names[d] for d in master.work_days_list())
    status = "активен ✅" if master.is_active else "скрыт ⛔"

    text = (
        f"👨‍🔧 {master.name}\n"
        f"Статус: {status}\n"
        f"График: {days_str}\n"
        f"Часы: {master.work_start}–{master.work_end}\n"
        f"Слот: {master.slot_duration} мин"
    )
    await callback.message.answer(text, reply_markup=admin_master_card_kb(master))
    await callback.answer()


@router.callback_query(AdminMasterCB.filter(F.action == "toggle"))
async def master_toggle(callback: CallbackQuery, callback_data: AdminMasterCB):
    await toggle_master_active(callback_data.id)
    master = await get_master(callback_data.id)
    await callback.message.edit_reply_markup(reply_markup=admin_master_card_kb(master))
    await callback.answer("Статус обновлён")


@router.callback_query(AdminMasterCB.filter(F.action == "delete"))
async def master_delete(callback: CallbackQuery, callback_data: AdminMasterCB):
    await delete_master(callback_data.id)
    await callback.message.edit_text("🗑 Мастер удалён.")
    await callback.answer()


# ---------------- SERVICES ----------------

@router.message(F.text == "🛠 Услуги")
async def services_list(message: Message):
    services = await get_all_services()
    await message.answer(
        "Услуги:" if services else "Пока нет ни одной услуги.",
        reply_markup=admin_services_list_kb(services),
    )


@router.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Введите название услуги (например «Стрижка кошки»):")
    await state.set_state(AdminAddService.waiting_name)
    await callback.answer()


@router.message(AdminAddService.waiting_name)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Цена услуги в рублях? Например 1500")
    await state.set_state(AdminAddService.waiting_price)


@router.message(AdminAddService.waiting_price)
async def add_service_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Введите цену числом, например 1500")
        return
    await state.update_data(price=int(message.text.strip()))
    await message.answer("Длительность услуги в минутах? Например 60")
    await state.set_state(AdminAddService.waiting_duration)


@router.message(AdminAddService.waiting_duration)
async def add_service_duration(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Введите число минут, например 60")
        return

    data = await state.get_data()
    service = await create_service(
        name=data["name"], price=data["price"], duration_minutes=int(message.text.strip())
    )
    await state.clear()
    await message.answer(f"✅ Услуга «{service.name}» добавлена!", reply_markup=admin_menu_kb())


@router.callback_query(AdminServiceCB.filter(F.action == "view"))
async def service_card(callback: CallbackQuery, callback_data: AdminServiceCB):
    service = await get_service(callback_data.id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    text = f"🛠 {service.name}\nЦена: {service.price}₽\nДлительность: {service.duration_minutes} мин"
    await callback.message.answer(text, reply_markup=admin_service_card_kb(service))
    await callback.answer()


@router.callback_query(AdminServiceCB.filter(F.action == "delete"))
async def service_delete(callback: CallbackQuery, callback_data: AdminServiceCB):
    await delete_service(callback_data.id)
    await callback.message.edit_text("🗑 Услуга удалена.")
    await callback.answer()


# ---------------- BOOKINGS BY DATE ----------------

@router.message(F.text == "📆 Записи на дату")
async def bookings_by_date_start(message: Message, state: FSMContext):
    await message.answer("Введите дату в формате ДД.ММ.ГГГГ (например 15.07.2026):")
    await state.set_state(AdminBookingsByDate.waiting_date)


@router.message(AdminBookingsByDate.waiting_date)
async def bookings_by_date_show(message: Message, state: FSMContext):
    try:
        date = dt.datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат. Введите дату как ДД.ММ.ГГГГ, например 15.07.2026")
        return

    bookings = await get_bookings_for_date(date)
    await state.clear()

    if not bookings:
        await message.answer(f"На {format_date_ru(date)} записей нет.", reply_markup=admin_menu_kb())
        return

    lines = [f"Записи на {format_date_ru(date)}:\n"]
    for b in bookings:
        service_line = f", {b.service.name}" if b.service else ""
        lines.append(f"• {b.time} — {b.master.name} — {b.user.full_name} ({b.user.phone}){service_line}")

    await message.answer("\n".join(lines))
    await message.answer("Отменить запись:", reply_markup=admin_bookings_list_kb(bookings))


@router.callback_query(AdminCancelBookingCB.filter())
async def admin_cancel_booking(callback: CallbackQuery, callback_data: AdminCancelBookingCB, bot: Bot):
    from gbot.database.requests import get_booking

    booking = await get_booking(callback_data.id)
    await cancel_booking(callback_data.id)
    await callback.message.edit_text("❌ Запись отменена администратором.")
    await callback.answer()

    if booking:
        try:
            await bot.send_message(
                booking.user.tg_id,
                f"⚠️ Ваша запись на {format_date_ru(booking.date)} в {booking.time} "
                f"к мастеру {booking.master.name} была отменена администратором. "
                "Пожалуйста, выберите другое время.",
            )
        except Exception:
            pass


# ---------------- BROADCAST ----------------

@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    await message.answer("Введите текст сообщения для рассылки всем клиентам:")
    await state.set_state(AdminBroadcast.waiting_text)


@router.message(AdminBroadcast.waiting_text)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    users = await get_all_users()
    await state.clear()

    sent, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(user.tg_id, f"📢 {text}")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"Рассылка завершена.\nОтправлено: {sent}\nНе доставлено: {failed}",
        reply_markup=admin_menu_kb(),
    )
