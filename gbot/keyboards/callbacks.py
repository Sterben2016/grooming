from aiogram.filters.callback_data import CallbackData


class MasterCB(CallbackData, prefix="master"):
    id: int


class ServiceCB(CallbackData, prefix="service"):
    id: int


class NoServiceCB(CallbackData, prefix="noservice"):
    pass


class DateCB(CallbackData, prefix="date"):
    iso: str  # YYYY-MM-DD


class TimeCB(CallbackData, prefix="time"):
    value: str  # HH:MM


class ConfirmBookingCB(CallbackData, prefix="confirm_booking"):
    action: str  # "yes" / "no"


class CancelBookingCB(CallbackData, prefix="cancel_booking"):
    id: int


# ---------- ADMIN ----------

class AdminMasterCB(CallbackData, prefix="a_master"):
    id: int
    action: str  # "view" / "toggle" / "delete"


class AdminServiceCB(CallbackData, prefix="a_service"):
    id: int
    action: str  # "view" / "delete"


class AdminDayToggleCB(CallbackData, prefix="a_day"):
    day: int  # 0-6


class AdminDayDoneCB(CallbackData, prefix="a_day_done"):
    pass


class AdminCancelBookingCB(CallbackData, prefix="a_cancel_booking"):
    id: int
