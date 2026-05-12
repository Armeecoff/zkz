from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from sqlalchemy import select
from bot.database.db import async_session, get_setting
from bot.database.models import User, Channel
from bot.keyboards.main import main_menu_kb, op_verify_kb
from bot.utils.helpers import get_or_create_user, credit_referral_bonus

router = Router()


async def send_main_menu(message: Message | CallbackQuery, edit: bool = False):
    welcome = await get_setting("welcome_text", "👋 Добро пожаловать!")
    photo = await get_setting("main_photo_file_id", "")
    kb = main_menu_kb()

    if isinstance(message, CallbackQuery):
        msg = message.message
        await message.answer()
    else:
        msg = message

    if photo:
        if edit and isinstance(message, CallbackQuery):
            try:
                await msg.delete()
            except Exception:
                pass
        await msg.answer_photo(photo=photo, caption=welcome, reply_markup=kb, parse_mode="HTML")
    else:
        if edit and isinstance(message, CallbackQuery):
            try:
                await msg.edit_text(welcome, reply_markup=kb, parse_mode="HTML")
                return
            except Exception:
                pass
        await msg.answer(welcome, reply_markup=kb, parse_mode="HTML")


@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split(" ", 1)
    referred_by = None
    partner_referred_by = None

    if len(args) > 1:
        param = args[1]
        if param.startswith("ref_"):
            try:
                referred_by = int(param[4:])
            except ValueError:
                pass
        elif param.startswith("partner_"):
            try:
                partner_referred_by = int(param[8:])
            except ValueError:
                pass

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        referred_by=referred_by,
        partner_referred_by=partner_referred_by,
    )

    async with async_session() as session:
        ch_result = await session.execute(
            select(Channel).where(Channel.is_active == True)
        )
        channels = ch_result.scalars().all()

    if channels and not user.op_verified:
        text = "📢 <b>Для использования бота необходимо подписаться на наши каналы:</b>"
        kb = op_verify_kb(channels)
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
        return

    await send_main_menu(message)


@router.callback_query(F.data == "check_op")
async def check_op(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with async_session() as session:
        ch_result = await session.execute(
            select(Channel).where(Channel.is_active == True)
        )
        channels = ch_result.scalars().all()

    not_subscribed = []
    for ch in channels:
        try:
            member = await callback.bot.get_chat_member(ch.channel_id, user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)

    if not_subscribed:
        await callback.answer("❌ Вы не подписаны на все каналы!", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if user and not user.op_verified:
            user.op_verified = True
            await session.commit()

            if user.referred_by:
                await credit_referral_bonus(
                    referrer_id=user.referred_by,
                    referred_id=user_id,
                    bonus_type="registration",
                    days=1,
                )
                try:
                    await callback.bot.send_message(
                        user.referred_by,
                        "🎉 Ваш реферал подписался на каналы! Вам начислен <b>1 бонусный день</b>.",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    await callback.answer("✅ Отлично! Добро пожаловать!")
    await send_main_menu(callback)


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    await send_main_menu(callback, edit=True)


@router.callback_query(F.data == "instruction")
async def show_instruction(callback: CallbackQuery):
    from bot.keyboards.main import back_to_main_kb
    text = await get_setting("instruction_text", "📖 Инструкция не настроена.")
    await callback.message.answer(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "our_channel")
async def our_channel(callback: CallbackQuery):
    link = await get_setting("channel_link", "")
    if not link:
        await callback.answer("Ссылка на канал не настроена.", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Перейти в канал", url=link)],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
    await callback.message.answer("📢 Наш официальный канал:", reply_markup=kb)
    await callback.answer()
