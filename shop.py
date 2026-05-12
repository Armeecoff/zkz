from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def shop_menu_kb(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"📦 {p.name} — {p.duration_days} дн.", callback_data=f"product:{p.id}")])
    buttons.append([InlineKeyboardButton(text="🎟 Мои промокоды", callback_data="my_promocodes")])
    buttons.append([InlineKeyboardButton(text="🔖 Активировать промокод", callback_data="activate_promo")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить себе", callback_data=f"buy_self:{product_id}")],
        [InlineKeyboardButton(text="🎁 Подарить", callback_data=f"buy_gift:{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="shop")],
    ])


def payment_method_kb(product_id: int, recipient_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 ЮКасса (рубли)", callback_data=f"pay_yookassa:{product_id}:{recipient_id}")],
        [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data=f"pay_stars:{product_id}:{recipient_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"product:{product_id}")],
    ])


def stars_invoice_kb(product_id: int, recipient_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"confirm_stars:{product_id}:{recipient_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="shop")],
    ])


def back_to_shop_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
