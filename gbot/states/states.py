from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


class Booking(StatesGroup):
    choosing_master = State()
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()


class AdminAddMaster(StatesGroup):
    waiting_name = State()
    waiting_days = State()
    waiting_start = State()
    waiting_end = State()
    waiting_duration = State()


class AdminAddService(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_duration = State()


class AdminBroadcast(StatesGroup):
    waiting_text = State()


class AdminBookingsByDate(StatesGroup):
    waiting_date = State()
