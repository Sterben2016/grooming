from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from gbot.database.requests import create_user, get_user_by_tg_id
from gbot.keyboards.client_kb import main_menu_kb, phone_request_kb
from gbot.states.states import Registration

router = Router(name="registration")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)

    if user:
        await message.answer(
            f"С возвращением, {user.full_name}! 🐾\n"
            "Выберите действие в меню ниже.",
            reply_markup=main_menu_kb(),
        )
        return

    await message.answer(
        "Добро пожаловать в груминг-салон для ваших питомцев! 🐶🐱\n\n"
        "Для начала давайте познакомимся. Как вас зовут?"
    )
    await state.set_state(Registration.waiting_name)


@router.message(Registration.waiting_name)
async def process_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите имя текстом (минимум 2 символа).")
        return

    await state.update_data(full_name=message.text.strip())
    await message.answer(
        "Отлично! Теперь поделитесь номером телефона, чтобы мы могли "
        "подтвердить запись — нажмите кнопку ниже.",
        reply_markup=phone_request_kb(),
    )
    await state.set_state(Registration.waiting_phone)


@router.message(Registration.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await finish_registration(message, state, message.contact.phone_number)


@router.message(Registration.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 5:
        await message.answer("Введите корректный номер телефона или нажмите кнопку отправки контакта.")
        return
    await finish_registration(message, state, phone)


async def finish_registration(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    full_name = data.get("full_name", message.from_user.full_name)

    await create_user(tg_id=message.from_user.id, full_name=full_name, phone=phone)
    await state.clear()

    await message.answer(
        f"Спасибо, {full_name}! Регистрация завершена. 🎉\n\n"
        "Теперь вы можете записаться на груминг для вашего питомца.",
        reply_markup=main_menu_kb(),
    )
