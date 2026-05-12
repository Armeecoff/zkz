from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def referral_kb(ref_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Поделиться реф. ссылкой", url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся+к+VPN+сервису!")],
        [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])


def partner_kb(partner_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Партнёрская ссылка", url=f"https://t.me/share/url?url={partner_link}&text=VPN+сервис+для+тебя!")],
        [InlineKeyboardButton(text="💸 Вывести средства", callback_data="withdraw_partner")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="referral")],
    ])


def withdraw_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить заявку", callback_data="confirm_withdrawal")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="partner")],
    ])
