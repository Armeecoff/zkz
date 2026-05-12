from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from bot.database.db import async_session, get_setting
from bot.database.models import User, WithdrawalRequest
from bot.keyboards.referral import referral_kb, partner_kb, withdraw_confirm_kb
from bot.keyboards.main import back_to_main_kb
from bot.utils.helpers import get_referral_stats, get_partner_stats
from bot.config import ADMIN_IDS

router = Router()


class WithdrawState(StatesGroup):
    waiting_details = State()
    waiting_amount = State()


@router.callback_query(F.data == "referral")
async def referral_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    stats = await get_referral_stats(user_id)
    photo = await get_setting("referral_photo_file_id", "")

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"<blockquote>"
        f"👤 Приглашено: <b>{stats['invited']}</b>\n"
        f"🎁 Бонусов за регистрацию: <b>{stats['reg_bonuses']}</b>\n"
        f"🛒 Бонусов за покупку: <b>{stats['purchase_bonuses']}</b>\n"
        f"📅 Всего бонусных дней: <b>{stats['total_bonus_days']}</b>\n"
        f"🗓 Текущий баланс: <b>{stats['current_bonus']} дн.</b>"
        f"</blockquote>\n\n"
        f"🔗 Ваша реф. ссылка:\n<code>{ref_link}</code>\n\n"
        f"За каждого приглашённого, кто подпишется на каналы — <b>+1 день</b>\n"
        f"За покупку подписки от 1 месяца — <b>+10 дней</b>"
    )

    kb = referral_kb(ref_link)
    if photo:
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "partner")
async def partner_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await callback.bot.get_me()
    partner_link = f"https://t.me/{bot_info.username}?start=partner_{user_id}"

    stats = await get_partner_stats(user_id)
    withdrawal_enabled = await get_setting("withdrawal_enabled", "1")
    min_withdrawal = await get_setting("min_withdrawal", "500")

    text = (
        f"🤝 <b>Партнёрская программа</b>\n\n"
        f"<blockquote>"
        f"✅ Подтверждённые рефералы: <b>{stats['confirmed']}</b>\n"
        f"🛒 Покупателей среди них: <b>{stats['buyers']}</b>\n"
        f"💰 Всего начислений: <b>{stats['total_credited']:.2f} ₽</b>\n"
        f"✅ Уже выведено: <b>{stats['withdrawn']:.2f} ₽</b>\n"
        f"💵 Доступно к выводу: <b>{stats['available']:.2f} ₽</b>"
        f"</blockquote>\n\n"
        f"🔗 Ваша партнёрская ссылка:\n<code>{partner_link}</code>\n\n"
        f"Вы получаете <b>30%</b> от каждой покупки ваших рефералов.\n"
        f"Мин. сумма вывода: <b>{min_withdrawal} ₽</b>"
    )
    if withdrawal_enabled != "1":
        text += "\n\n⛔ <i>Вывод временно недоступен.</i>"

    kb = partner_kb(partner_link)
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "withdraw_partner")
async def withdraw_partner(callback: CallbackQuery, state: FSMContext):
    withdrawal_enabled = await get_setting("withdrawal_enabled", "1")
    if withdrawal_enabled != "1":
        await callback.answer("⛔ Вывод временно недоступен.", show_alert=True)
        return

    stats = await get_partner_stats(callback.from_user.id)
    min_withdrawal = float(await get_setting("min_withdrawal", "500"))

    if stats["available"] < min_withdrawal:
        await callback.answer(
            f"❌ Минимальная сумма вывода: {min_withdrawal:.0f} ₽\nВаш баланс: {stats['available']:.2f} ₽",
            show_alert=True
        )
        return

    await state.update_data(available=stats["available"])
    await state.set_state(WithdrawState.waiting_amount)
    await callback.message.answer(
        f"💸 <b>Вывод средств</b>\n\n"
        f"Доступно: <b>{stats['available']:.2f} ₽</b>\n"
        f"Введите сумму вывода:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(WithdrawState.waiting_amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    available = data.get("available", 0)
    min_withdrawal = float(await get_setting("min_withdrawal", "500"))

    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректную сумму:")
        return

    if amount < min_withdrawal:
        await message.answer(f"❌ Минимальная сумма вывода: {min_withdrawal:.0f} ₽")
        return

    if amount > available:
        await message.answer(f"❌ Недостаточно средств. Доступно: {available:.2f} ₽")
        return

    await state.update_data(withdraw_amount=amount)
    await state.set_state(WithdrawState.waiting_details)
    await message.answer(
        f"💳 <b>Введите реквизиты для вывода {amount:.2f} ₽:</b>\n\n"
        "Например: Сбербанк / 4276 XXXX XXXX XXXX / Иванов Иван",
        parse_mode="HTML"
    )


@router.message(WithdrawState.waiting_details)
async def process_withdraw_details(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("withdraw_amount", 0)
    details = message.text.strip()
    user_id = message.from_user.id

    await state.update_data(withdraw_details=details)
    await message.answer(
        f"💸 <b>Подтверждение вывода</b>\n\n"
        f"Сумма: <b>{amount:.2f} ₽</b>\n"
        f"Реквизиты: <b>{details}</b>",
        reply_markup=withdraw_confirm_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_withdrawal")
async def confirm_withdrawal(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("withdraw_amount", 0)
    details = data.get("withdraw_details", "")
    user_id = callback.from_user.id

    async with async_session() as session:
        u_result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = u_result.scalar_one_or_none()
        if not user or user.partner_balance < amount:
            await callback.answer("❌ Недостаточно средств.", show_alert=True)
            await state.clear()
            return

        user.partner_balance -= amount

        req = WithdrawalRequest(
            user_telegram_id=user_id,
            amount=amount,
            details=details,
            status="pending"
        )
        session.add(req)
        await session.commit()
        req_id = req.id

    await callback.message.answer(
        "✅ <b>Заявка на вывод отправлена!</b>\n\nАдминистратор рассмотрит её в ближайшее время.",
        reply_markup=back_to_main_kb(), parse_mode="HTML"
    )

    username = callback.from_user.username or "—"
    for admin_id in ADMIN_IDS:
        try:
            from bot.keyboards.admin import admin_withdrawal_kb
            await callback.bot.send_message(
                admin_id,
                f"💸 <b>Заявка на вывод #{req_id}</b>\n\n"
                f"Пользователь: @{username} (<code>{user_id}</code>)\n"
                f"Сумма: <b>{amount:.2f} ₽</b>\n"
                f"Реквизиты: {details}",
                reply_markup=admin_withdrawal_kb(req_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

    await state.clear()
    await callback.answer()
