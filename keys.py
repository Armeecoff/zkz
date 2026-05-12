from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from bot.database.db import async_session
from bot.database.models import UserSubscription, VpnKey, Product
from bot.keyboards.main import key_detail_kb, back_to_main_kb, main_menu_kb

router = Router()


@router.callback_query(F.data == "my_keys")
async def my_keys(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserSubscription)
            .options(selectinload(UserSubscription.vpn_key), selectinload(UserSubscription.product))
            .where(
                UserSubscription.user_telegram_id == user_id,
                UserSubscription.is_active == True,
            )
        )
        subs = result.scalars().all()

    if not subs:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить подписку", callback_data="shop")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ])
        await callback.message.answer(
            "🔑 <b>У вас нет активных ключей.</b>\n\nПриобретите подписку, чтобы получить ключ.",
            reply_markup=kb, parse_mode="HTML"
        )
        await callback.answer()
        return

    for sub in subs:
        now = datetime.utcnow()
        if sub.expires_at < now:
            continue
        days_left = (sub.expires_at - now).days
        hours_left = int((sub.expires_at - now).total_seconds() // 3600) % 24
        key = sub.vpn_key
        product = sub.product

        text = (
            f"🔑 <b>{product.name if product else 'Подписка'}</b>\n\n"
            f"⏰ Осталось: <b>{days_left} дн. {hours_left} ч.</b>\n"
            f"📅 До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b>\n\n"
            f"🔗 Ключ:\n<code>{key.key_value if key else 'N/A'}</code>"
        )
        if sub.is_gift:
            text += "\n\n🎁 <i>Подарок</i>"

        await callback.message.answer(text, reply_markup=key_detail_kb(sub.id), parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data.startswith("key_copy:"))
async def key_copy(callback: CallbackQuery):
    sub_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(
            select(UserSubscription)
            .options(selectinload(UserSubscription.vpn_key))
            .where(
                UserSubscription.id == sub_id,
                UserSubscription.user_telegram_id == callback.from_user.id
            )
        )
        sub = result.scalar_one_or_none()

    if not sub or not sub.vpn_key:
        await callback.answer("Ключ не найден.", show_alert=True)
        return

    await callback.message.answer(
        f"📋 Ваш ключ:\n\n<code>{sub.vpn_key.key_value}</code>",
        parse_mode="HTML"
    )
    await callback.answer("✅ Скопируйте ключ выше")


@router.callback_query(F.data.startswith("key_open_link:"))
async def key_open_link(callback: CallbackQuery):
    sub_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(
            select(UserSubscription)
            .options(selectinload(UserSubscription.vpn_key))
            .where(
                UserSubscription.id == sub_id,
                UserSubscription.user_telegram_id == callback.from_user.id
            )
        )
        sub = result.scalar_one_or_none()

    if not sub or not sub.vpn_key:
        await callback.answer("Ключ не найден.", show_alert=True)
        return

    link = sub.vpn_key.key_link or sub.vpn_key.key_value
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть", url=link)],
    ])
    await callback.message.answer("🔗 Ссылка вашего ключа:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("key_extend:"))
async def key_extend(callback: CallbackQuery):
    sub_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(
            select(UserSubscription)
            .options(selectinload(UserSubscription.product))
            .where(
                UserSubscription.id == sub_id,
                UserSubscription.user_telegram_id == callback.from_user.id
            )
        )
        sub = result.scalar_one_or_none()

    if not sub:
        await callback.answer("Подписка не найдена.", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer(
        "🔄 Чтобы продлить подписку, перейдите в магазин и выберите нужный тариф.",
        reply_markup=back_to_main_kb()
    )
