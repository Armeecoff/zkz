from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def support_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать тикет", callback_data="create_ticket")],
        [InlineKeyboardButton(text="📋 Мои тикеты", callback_data="my_tickets")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])


def ticket_detail_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написать сообщение", callback_data=f"ticket_reply:{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"ticket_close:{ticket_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_tickets")],
    ])


def my_tickets_kb(tickets: list) -> InlineKeyboardMarkup:
    buttons = []
    for t in tickets:
        status_icon = "🟢" if t.status == "open" else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} #{t.id} {t.subject[:25]}",
            callback_data=f"view_ticket:{t.id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
