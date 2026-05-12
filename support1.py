from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bot.database.db import async_session
from bot.database.models import SupportTicket, TicketMessage
from bot.keyboards.support import support_menu_kb, ticket_detail_kb, my_tickets_kb
from bot.keyboards.main import back_to_main_kb
from bot.config import ADMIN_IDS

router = Router()


class SupportStates(StatesGroup):
    waiting_subject = State()
    waiting_message = State()
    waiting_reply = State()


@router.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery):
    await callback.message.answer(
        "🛡 <b>Поддержка</b>\n\n"
        "Создайте тикет, и наши специалисты ответят вам в ближайшее время.",
        reply_markup=support_menu_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "create_ticket")
async def create_ticket(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_subject)
    await callback.message.answer("📝 <b>Введите тему обращения:</b>", parse_mode="HTML")
    await callback.answer()


@router.message(SupportStates.waiting_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await state.set_state(SupportStates.waiting_message)
    await message.answer("✉️ <b>Опишите вашу проблему:</b>", parse_mode="HTML")


@router.message(SupportStates.waiting_message)
async def process_ticket_message(message: Message, state: FSMContext):
    data = await state.get_data()
    subject = data.get("subject", "Без темы")
    user_id = message.from_user.id

    async with async_session() as session:
        ticket = SupportTicket(
            user_telegram_id=user_id,
            subject=subject,
            status="open"
        )
        session.add(ticket)
        await session.flush()

        msg = TicketMessage(
            ticket_id=ticket.id,
            sender_id=user_id,
            is_admin=False,
            message=message.text,
        )
        session.add(msg)
        await session.commit()
        ticket_id = ticket.id

    await message.answer(
        f"✅ <b>Тикет #{ticket_id} создан!</b>\n\nМы ответим вам как можно скорее.",
        reply_markup=back_to_main_kb(), parse_mode="HTML"
    )

    username = message.from_user.username or "—"
    for admin_id in ADMIN_IDS:
        try:
            from bot.keyboards.admin import admin_ticket_kb
            await message.bot.send_message(
                admin_id,
                f"📨 <b>Новый тикет #{ticket_id}</b>\n\n"
                f"Пользователь: @{username} (<code>{user_id}</code>)\n"
                f"Тема: <b>{subject}</b>\n\n"
                f"Сообщение:\n{message.text}",
                reply_markup=admin_ticket_kb(ticket_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

    await state.clear()


@router.callback_query(F.data == "my_tickets")
async def my_tickets(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(SupportTicket)
            .where(SupportTicket.user_telegram_id == user_id)
            .order_by(SupportTicket.created_at.desc())
            .limit(20)
        )
        tickets = result.scalars().all()

    if not tickets:
        await callback.message.answer(
            "📋 <b>У вас нет тикетов.</b>",
            reply_markup=support_menu_kb(), parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.message.answer(
        "📋 <b>Ваши тикеты:</b>",
        reply_markup=my_tickets_kb(tickets), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_ticket:"))
async def view_ticket(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(SupportTicket)
            .options(selectinload(SupportTicket.messages))
            .where(SupportTicket.id == ticket_id, SupportTicket.user_telegram_id == user_id)
        )
        ticket = result.scalar_one_or_none()

    if not ticket:
        await callback.answer("Тикет не найден.", show_alert=True)
        return

    text = f"📋 <b>Тикет #{ticket.id}: {ticket.subject}</b>\nСтатус: {'🟢 Открыт' if ticket.status == 'open' else '🔴 Закрыт'}\n\n"
    for m in ticket.messages:
        sender = "🛡 Поддержка" if m.is_admin else "👤 Вы"
        text += f"<b>{sender}:</b> {m.message}\n\n"

    await callback.message.answer(
        text,
        reply_markup=ticket_detail_kb(ticket_id) if ticket.status == "open" else back_to_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_reply:"))
async def ticket_reply(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split(":")[1])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(SupportStates.waiting_reply)
    await callback.message.answer(f"✉️ <b>Напишите ответ для тикета #{ticket_id}:</b>", parse_mode="HTML")
    await callback.answer()


@router.message(SupportStates.waiting_reply)
async def process_user_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    user_id = message.from_user.id

    async with async_session() as session:
        ticket_result = await session.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id, SupportTicket.user_telegram_id == user_id)
        )
        ticket = ticket_result.scalar_one_or_none()
        if not ticket:
            await message.answer("Тикет не найден.")
            await state.clear()
            return

        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_id=user_id,
            is_admin=False,
            message=message.text,
        )
        session.add(msg)
        await session.commit()

    await message.answer("✅ Сообщение отправлено.", reply_markup=back_to_main_kb())

    username = message.from_user.username or "—"
    for admin_id in ADMIN_IDS:
        try:
            from bot.keyboards.admin import admin_ticket_kb
            await message.bot.send_message(
                admin_id,
                f"💬 <b>Новое сообщение в тикете #{ticket_id}</b>\n\n"
                f"От: @{username} (<code>{user_id}</code>)\n\n"
                f"{message.text}",
                reply_markup=admin_ticket_kb(ticket_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

    await state.clear()


@router.callback_query(F.data.startswith("ticket_close:"))
async def ticket_close(callback: CallbackQuery):
    ticket_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id, SupportTicket.user_telegram_id == user_id)
        )
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.status = "closed"
            await session.commit()

    await callback.message.answer("✅ Тикет закрыт.", reply_markup=back_to_main_kb())
    await callback.answer()
