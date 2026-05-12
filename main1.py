from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Ваш ключ", callback_data="my_keys")],
        [InlineKeyboardButton(text="🛒 Купить подписку", callback_data="shop")],
        [InlineKeyboardButton(text="👥 Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner")],
        [InlineKeyboardButton(text="🛡 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="📢 Наш канал", callback_data="our_channel")],
    ])


def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def key_detail_kb(subscription_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть ссылку", callback_data=f"key_open_link:{subscription_id}")],
        [InlineKeyboardButton(text="📋 Скопировать ключ", callback_data=f"key_copy:{subscription_id}")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data=f"key_extend:{subscription_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])


def op_verify_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        link = ch.invite_link or f"https://t.me/{ch.channel_id.lstrip('@')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {ch.title}", url=link)])
    buttons.append([InlineKeyboardButton(text="✅ Я подписался", callback_data="check_op")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
