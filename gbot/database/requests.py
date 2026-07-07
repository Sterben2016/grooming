import datetime as dt

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from gbot.database.db import async_session
from gbot.database.models import Booking, Master, Service, User


# ---------- USERS ----------

async def get_user_by_tg_id(tg_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()


async def create_user(tg_id: int, full_name: str, phone: str) -> User:
    async with async_session() as session:
        user = User(tg_id=tg_id, full_name=full_name, phone=phone)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User))
        return list(result.scalars().all())


# ---------- MASTERS ----------

async def get_active_masters() -> list[Master]:
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())


async def get_all_masters() -> list[Master]:
    async with async_session() as session:
        result = await session.execute(select(Master))
        return list(result.scalars().all())


async def get_master(master_id: int) -> Master | None:
    async with async_session() as session:
        result = await session.execute(select(Master).where(Master.id == master_id))
        return result.scalar_one_or_none()


async def create_master(
    name: str, work_days: str, work_start: str, work_end: str, slot_duration: int
) -> Master:
    async with async_session() as session:
        master = Master(
            name=name,
            work_days=work_days,
            work_start=work_start,
            work_end=work_end,
            slot_duration=slot_duration,
        )
        session.add(master)
        await session.commit()
        await session.refresh(master)
        return master


async def toggle_master_active(master_id: int) -> None:
    async with async_session() as session:
        master = await session.get(Master, master_id)
        if master:
            master.is_active = not master.is_active
            await session.commit()


async def delete_master(master_id: int) -> None:
    async with async_session() as session:
        master = await session.get(Master, master_id)
        if master:
            await session.delete(master)
            await session.commit()


# ---------- SERVICES ----------

async def get_active_services() -> list[Service]:
    async with async_session() as session:
        result = await session.execute(
            select(Service).where(Service.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())


async def get_all_services() -> list[Service]:
    async with async_session() as session:
        result = await session.execute(select(Service))
        return list(result.scalars().all())


async def get_service(service_id: int) -> Service | None:
    async with async_session() as session:
        result = await session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()


async def create_service(name: str, price: int, duration_minutes: int) -> Service:
    async with async_session() as session:
        service = Service(name=name, price=price, duration_minutes=duration_minutes)
        session.add(service)
        await session.commit()
        await session.refresh(service)
        return service


async def delete_service(service_id: int) -> None:
    async with async_session() as session:
        service = await session.get(Service, service_id)
        if service:
            await session.delete(service)
            await session.commit()


# ---------- BOOKINGS ----------

async def get_booked_times(master_id: int, date: dt.date) -> list[str]:
    async with async_session() as session:
        result = await session.execute(
            select(Booking.time).where(
                Booking.master_id == master_id,
                Booking.date == date,
                Booking.status == "active",
            )
        )
        return [row[0] for row in result.all()]


async def create_booking(
    user_id: int, master_id: int, service_id: int | None, date: dt.date, time: str
) -> Booking:
    async with async_session() as session:
        booking = Booking(
            user_id=user_id,
            master_id=master_id,
            service_id=service_id,
            date=date,
            time=time,
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking


async def get_user_active_bookings(user_id: int) -> list[Booking]:
    async with async_session() as session:
        result = await session.execute(
            select(Booking)
            .options(selectinload(Booking.master), selectinload(Booking.service))
            .where(
                Booking.user_id == user_id,
                Booking.status == "active",
                Booking.date >= dt.date.today(),
            )
            .order_by(Booking.date, Booking.time)
        )
        return list(result.scalars().all())


async def get_booking(booking_id: int) -> Booking | None:
    async with async_session() as session:
        result = await session.execute(
            select(Booking)
            .options(selectinload(Booking.master), selectinload(Booking.service), selectinload(Booking.user))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()


async def cancel_booking(booking_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(Booking).where(Booking.id == booking_id).values(status="cancelled")
        )
        await session.commit()


async def get_bookings_for_date(date: dt.date) -> list[Booking]:
    async with async_session() as session:
        result = await session.execute(
            select(Booking)
            .options(selectinload(Booking.master), selectinload(Booking.service), selectinload(Booking.user))
            .where(Booking.date == date, Booking.status == "active")
            .order_by(Booking.master_id, Booking.time)
        )
        return list(result.scalars().all())
