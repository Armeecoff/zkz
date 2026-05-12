from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Товары / Ключи", callback_data="adm_products")],
        [InlineKeyboardButton(text="🎟 Промокоды", callback_data="adm_promocodes")],
        [InlineKeyboardButton(text="📢 Каналы ОП", callback_data="adm_channels")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="adm_settings")],
        [InlineKeyboardButton(text="🖼 Фото разделов", callback_data="adm_photos")],
        [InlineKeyboardButton(text="🛡 Поддержка", callback_data="adm_support")],
        [InlineKeyboardButton(text="💸 Заявки на вывод", callback_data="adm_withdrawals")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
    ])


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        status = "✅" if p.is_active else "❌"
        buttons.append([InlineKeyboardButton(text=f"{status} {p.name}", callback_data=f"adm_product:{p.id}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить товар", callback_data="adm_add_product")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_detail_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Добавить ключи", callback_data=f"adm_add_keys:{product_id}")],
        [InlineKeyboardButton(text="📋 Список ключей", callback_data=f"adm_list_keys:{product_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"adm_edit_product:{product_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del_product:{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_products")],
    ])


def admin_channels_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        status = "✅" if ch.is_active else "❌"
        buttons.append([InlineKeyboardButton(text=f"{status} {ch.title}", callback_data=f"adm_channel:{ch.id}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="adm_add_channel")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_channel_detail_kb(channel_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del_channel:{channel_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_channels")],
    ])


def admin_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱ Пробный период (часы)", callback_data="adm_set_trial")],
        [InlineKeyboardButton(text="📖 Текст инструкции", callback_data="adm_set_instruction")],
        [InlineKeyboardButton(text="📢 Ссылка на канал", callback_data="adm_set_channel_link")],
        [InlineKeyboardButton(text="💬 Ссылка поддержки", callback_data="adm_set_support_link")],
        [InlineKeyboardButton(text="💸 Мин. сумма вывода", callback_data="adm_set_min_withdrawal")],
        [InlineKeyboardButton(text="🔛 Вывод вкл/выкл", callback_data="adm_toggle_withdrawal")],
        [InlineKeyboardButton(text="👋 Приветственный текст", callback_data="adm_set_welcome")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")],
    ])


def admin_photos_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Фото главного меню", callback_data="adm_photo_main")],
        [InlineKeyboardButton(text="🛒 Фото магазина", callback_data="adm_photo_shop")],
        [InlineKeyboardButton(text="👥 Фото реферальной", callback_data="adm_photo_referral")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")],
    ])


def admin_promocodes_kb(promos: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in promos:
        status = "✅" if p.is_active else "❌"
        buttons.append([InlineKeyboardButton(text=f"{status} {p.code}", callback_data=f"adm_promo:{p.id}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить промокод", callback_data="adm_add_promo")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_promo_detail_kb(promo_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del_promo:{promo_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_promocodes")],
    ])


def admin_support_tickets_kb(tickets: list) -> InlineKeyboardMarkup:
    buttons = []
    for t in tickets:
        buttons.append([InlineKeyboardButton(
            text=f"#{t.id} {t.subject[:30]} [{t.status}]",
            callback_data=f"adm_ticket:{t.id}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_ticket_kb(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Ответить", callback_data=f"adm_reply_ticket:{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"adm_close_ticket:{ticket_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_support")],
    ])


def admin_withdrawal_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"adm_withdraw_approve:{request_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_withdraw_reject:{request_id}")],
        [InlineKeyboardButton(text="↩️ Возврат", callback_data=f"adm_withdraw_refund:{request_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_withdrawals")],
    ])
