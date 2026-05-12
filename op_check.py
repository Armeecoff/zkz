from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User, Channel
from bot.keyboards.main import op_verify_kb


class OPCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            callback_data = ""
            if isinstance(event, CallbackQuery):
                callback_data = event.data or ""

            skip_callbacks = {"check_op", "main_menu"}
            if any(callback_data.startswith(s) for s in skip_callbacks):
                return await handler(event, data)

            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user or not user.op_verified:
                    ch_result = await session.execute(
                        select(Channel).where(Channel.is_active == True)
                    )
                    channels = ch_result.scalars().all()

                    if channels:
                        text = "📢 <b>Для использования бота необходимо подписаться на наши каналы:</b>"
                        kb = op_verify_kb(channels)
                        if isinstance(event, Message):
                            await event.answer(text, reply_markup=kb, parse_mode="HTML")
                        elif isinstance(event, CallbackQuery):
                            await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
                            await event.answer()
                        return

        return await handler(event, data)
