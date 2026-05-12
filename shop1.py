from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bot.database.db import async_session, get_setting
from bot.database.models import Product, PromoCode, UserPromoCode, Payment, User
from bot.keyboards.shop import (
    shop_menu_kb, product_detail_kb, payment_method_kb,
    stars_invoice_kb, back_to_shop_kb
)
from bot.keyboards.main import back_to_main_kb
from bot.utils.helpers import assign_key_to_user, get_available_keys_count, credit_referral_bonus, credit_partner_bonus
from bot.utils.payments import create_yookassa_payment

router = Router()


class ShopStates(StatesGroup):
    waiting_gift_id = State()
    waiting_promo_code = State()


@router.callback_query(F.data == "shop")
async def shop_menu(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.is_active == True)
        )
        products = result.scalars().all()

    photo = await get_setting("shop_photo_file_id", "")
    text = "🛒 <b>Магазин подписок</b>\n\nВыберите тариф:"
    kb = shop_menu_kb(products)

    if photo:
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    available = await get_available_keys_count(product_id)
    text = (
        f"📦 <b>{product.name}</b>\n\n"
        f"⏰ Срок: <b>{product.duration_days} дней</b>\n"
        f"💵 Цена: <b>{product.price_rub:.0f} ₽</b> / <b>{product.price_stars} ⭐</b>\n"
        f"🔑 Доступно ключей: <b>{available}</b>\n\n"
        f"{product.description or ''}"
    )
    kb = product_detail_kb(product_id)

    if product.photo_file_id:
        await callback.message.answer_photo(photo=product.photo_file_id, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("buy_self:"))
async def buy_self(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "💳 <b>Выберите способ оплаты:</b>",
        reply_markup=payment_method_kb(product_id, 0),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_gift:"))
async def buy_gift(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.update_data(gift_product_id=product_id)
    await state.set_state(ShopStates.waiting_gift_id)
    await callback.message.answer(
        "🎁 <b>Введите ID или @username получателя подарка:</b>\n\n"
        "Например: <code>123456789</code> или <code>@username</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ShopStates.waiting_gift_id)
async def process_gift_id(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("gift_product_id")
    recipient_id = 0
    text = message.text.strip()

    if text.startswith("@"):
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.username == text[1:])
            )
            recipient = result.scalar_one_or_none()
            if recipient:
                recipient_id = recipient.telegram_id
    else:
        try:
            recipient_id = int(text)
        except ValueError:
            pass

    if not recipient_id:
        await message.answer("❌ Пользователь не найден. Введите корректный ID или @username:")
        return

    await state.clear()
    await message.answer(
        f"🎁 Подарок для пользователя <code>{recipient_id}</code>\n\n💳 <b>Выберите способ оплаты:</b>",
        reply_markup=payment_method_kb(product_id, recipient_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_yookassa:"))
async def pay_yookassa(callback: CallbackQuery):
    _, product_id_str, recipient_id_str = callback.data.split(":")
    product_id = int(product_id_str)
    recipient_id = int(recipient_id_str)

    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    payment_data = create_yookassa_payment(
        amount=product.price_rub,
        description=f"Подписка {product.name}",
    )

    if not payment_data:
        await callback.answer("Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        return

    async with async_session() as session:
        payment = Payment(
            user_telegram_id=callback.from_user.id,
            product_id=product_id,
            amount_rub=product.price_rub,
            payment_method="yookassa",
            payment_id=payment_data["id"],
            status="pending",
            recipient_telegram_id=recipient_id if recipient_id else callback.from_user.id,
        )
        session.add(payment)
        await session.commit()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_data["url"])],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_yookassa:{payment_data['id']}:{product_id}:{recipient_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="shop")],
    ])
    await callback.message.answer(
        f"💳 <b>Оплата через ЮКассу</b>\n\n"
        f"📦 Товар: {product.name}\n"
        f"💵 Сумма: {product.price_rub:.0f} ₽\n\n"
        "Нажмите кнопку ниже для перехода к оплате, затем нажмите «Проверить оплату».",
        reply_markup=kb, parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("check_yookassa:"))
async def check_yookassa(callback: CallbackQuery):
    parts = callback.data.split(":")
    payment_id = parts[1]
    product_id = int(parts[2])
    recipient_id = int(parts[3])

    from bot.utils.payments import check_yookassa_payment
    status = check_yookassa_payment(payment_id)

    if status != "succeeded":
        await callback.answer("⏳ Оплата ещё не поступила. Попробуйте через несколько секунд.", show_alert=True)
        return

    async with async_session() as session:
        p_result = await session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        payment = p_result.scalar_one_or_none()
        if payment:
            payment.status = "paid"
            await session.commit()

    target_user = recipient_id if recipient_id else callback.from_user.id
    await _deliver_key(callback, product_id, target_user, callback.from_user.id)


@router.callback_query(F.data.startswith("pay_stars:"))
async def pay_stars(callback: CallbackQuery):
    _, product_id_str, recipient_id_str = callback.data.split(":")
    product_id = int(product_id_str)
    recipient_id = int(recipient_id_str)

    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=product.name,
        description=f"Подписка на {product.duration_days} дней",
        payload=f"stars:{product_id}:{recipient_id}:{callback.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label=product.name, amount=product.price_stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split(":")
    if parts[0] == "stars":
        product_id = int(parts[1])
        recipient_id = int(parts[2])
        buyer_id = int(parts[3])

        async with async_session() as session:
            prod_result = await session.execute(select(Product).where(Product.id == product_id))
            product = prod_result.scalar_one_or_none()

        payment = Payment(
            user_telegram_id=buyer_id,
            product_id=product_id,
            amount_stars=message.successful_payment.total_amount,
            payment_method="stars",
            payment_id=message.successful_payment.telegram_payment_charge_id,
            status="paid",
            recipient_telegram_id=recipient_id if recipient_id else buyer_id,
        )
        async with async_session() as session:
            session.add(payment)
            await session.commit()

        target_user = recipient_id if recipient_id else buyer_id

        async with async_session() as session:
            prod_result = await session.execute(select(Product).where(Product.id == product_id))
            product = prod_result.scalar_one_or_none()

        sub = await assign_key_to_user(target_user, product_id, product.duration_days, is_gift=(target_user != buyer_id), gift_from=buyer_id if target_user != buyer_id else None)

        if sub:
            async with async_session() as session:
                from sqlalchemy.orm import selectinload
                result = await session.execute(
                    select(sub.__class__).options(selectinload(sub.__class__.vpn_key)).where(sub.__class__.id == sub.id)
                )
                sub = result.scalar_one()

            key_val = sub.vpn_key.key_value if sub.vpn_key else "N/A"
            if target_user == buyer_id:
                await message.answer(
                    f"✅ <b>Оплата прошла! Ваш ключ:</b>\n\n<code>{key_val}</code>",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"✅ <b>Подарок отправлен!</b> Получатель получил свой ключ.",
                    parse_mode="HTML"
                )
                try:
                    await message.bot.send_message(
                        target_user,
                        f"🎁 <b>Вам подарили подписку!</b>\n\nВаш ключ:\n<code>{key_val}</code>",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            await _process_referral_bonuses(buyer_id, product, message.bot)
        else:
            await message.answer("❌ Ключи закончились. Свяжитесь с поддержкой.")


async def _deliver_key(callback: CallbackQuery, product_id: int, target_user: int, buyer_id: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    is_gift = target_user != buyer_id
    sub = await assign_key_to_user(target_user, product_id, product.duration_days, is_gift=is_gift, gift_from=buyer_id if is_gift else None)

    if not sub:
        await callback.message.answer("❌ Ключи для данного товара закончились. Свяжитесь с поддержкой.")
        await callback.answer()
        return

    async with async_session() as session:
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(sub.__class__).options(selectinload(sub.__class__.vpn_key)).where(sub.__class__.id == sub.id)
        )
        sub = result.scalar_one()

    key_val = sub.vpn_key.key_value if sub.vpn_key else "N/A"
    if not is_gift:
        await callback.message.answer(
            f"✅ <b>Оплата прошла! Ваш ключ:</b>\n\n<code>{key_val}</code>",
            reply_markup=back_to_main_kb(), parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            f"✅ <b>Подарок отправлен пользователю {target_user}!</b>",
            reply_markup=back_to_main_kb(), parse_mode="HTML"
        )
        try:
            await callback.bot.send_message(
                target_user,
                f"🎁 <b>Вам подарили подписку!</b>\n\nВаш ключ:\n<code>{key_val}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await _process_referral_bonuses(buyer_id, product, callback.bot)
    await callback.answer()


async def _process_referral_bonuses(buyer_id: int, product, bot):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == buyer_id))
        user = result.scalar_one_or_none()

    if user and user.referred_by and product.duration_days >= 30:
        await credit_referral_bonus(
            referrer_id=user.referred_by,
            referred_id=buyer_id,
            bonus_type="purchase",
            days=10,
        )
        try:
            await bot.send_message(
                user.referred_by,
                f"🎉 Ваш реферал купил подписку! Вам начислено <b>10 бонусных дней</b>.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    if user and user.partner_referred_by:
        rub_amount = product.price_rub or 0
        if rub_amount > 0:
            await credit_partner_bonus(
                referrer_id=user.partner_referred_by,
                referred_id=buyer_id,
                amount=rub_amount,
            )
            async with async_session() as session:
                p_result = await session.execute(select(User).where(User.telegram_id == user.partner_referred_by))
                partner = p_result.scalar_one_or_none()
            bonus = round(rub_amount * 0.30, 2)
            try:
                await bot.send_message(
                    user.partner_referred_by,
                    f"💰 Ваш партнёр совершил покупку! Вам начислено <b>{bonus} ₽</b> (30%).",
                    parse_mode="HTML"
                )
            except Exception:
                pass


@router.callback_query(F.data == "my_promocodes")
async def my_promocodes(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserPromoCode)
            .options(selectinload(UserPromoCode.product), selectinload(UserPromoCode.promo_code))
            .where(
                UserPromoCode.user_telegram_id == user_id,
                UserPromoCode.is_used == False
            )
        )
        promos = result.scalars().all()

    if not promos:
        await callback.message.answer(
            "🎟 <b>У вас нет активных промокодов.</b>",
            reply_markup=back_to_shop_kb(), parse_mode="HTML"
        )
        await callback.answer()
        return

    text = "🎟 <b>Ваши промокоды:</b>\n\n"
    for up in promos:
        product_name = up.product.name if up.product else "Подписка"
        text += f"• <code>{up.promo_code.code}</code> — {product_name}\n"
    text += "\nДля активации нажмите «Активировать промокод»."

    await callback.message.answer(text, reply_markup=back_to_shop_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "activate_promo")
async def activate_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.waiting_promo_code)
    await callback.message.answer(
        "🔖 Введите промокод:",
        reply_markup=back_to_shop_kb()
    )
    await callback.answer()


@router.message(ShopStates.waiting_promo_code)
async def process_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(PromoCode)
            .options(selectinload(PromoCode.product))
            .where(PromoCode.code == code, PromoCode.is_active == True)
        )
        promo = result.scalar_one_or_none()

    if not promo:
        await message.answer("❌ Промокод не найден или неактивен.", reply_markup=back_to_shop_kb())
        await state.clear()
        return

    if promo.used_count >= promo.max_uses:
        await message.answer("❌ Промокод уже использован максимальное количество раз.", reply_markup=back_to_shop_kb())
        await state.clear()
        return

    if promo.product_id:
        sub = await assign_key_to_user(user_id, promo.product_id, promo.product.duration_days)
        if not sub:
            await message.answer("❌ Ключи закончились. Обратитесь в поддержку.")
            await state.clear()
            return

        async with async_session() as session:
            result = await session.execute(select(PromoCode).where(PromoCode.id == promo.id))
            p = result.scalar_one()
            p.used_count += 1
            await session.commit()

        from sqlalchemy.orm import selectinload as slo
        async with async_session() as session:
            result = await session.execute(
                select(sub.__class__).options(slo(sub.__class__.vpn_key)).where(sub.__class__.id == sub.id)
            )
            sub = result.scalar_one()

        key_val = sub.vpn_key.key_value if sub.vpn_key else "N/A"
        await message.answer(
            f"✅ <b>Промокод активирован!</b>\n\nВаш ключ:\n<code>{key_val}</code>",
            parse_mode="HTML", reply_markup=back_to_shop_kb()
        )
    else:
        await message.answer(
            f"✅ <b>Промокод активирован!</b>\nСкидка: {promo.discount_percent}%",
            parse_mode="HTML", reply_markup=back_to_shop_kb()
        )

    await state.clear()
