from datetime import datetime, timedelta
from sqlalchemy import select, func
from bot.database.db import async_session
from bot.database.models import (
    User, VpnKey, UserSubscription, Product, ReferralBonus, Payment
)


async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None,
                              referred_by: int = None, partner_referred_by: int = None) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                referred_by=referred_by,
                partner_referred_by=partner_referred_by,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def assign_key_to_user(user_id: int, product_id: int, duration_days: int, is_gift: bool = False, gift_from: int = None) -> UserSubscription | None:
    async with async_session() as session:
        key_result = await session.execute(
            select(VpnKey).where(
                VpnKey.product_id == product_id,
                VpnKey.is_used == False
            ).limit(1)
        )
        key = key_result.scalar_one_or_none()
        if not key:
            return None

        key.is_used = True
        expires_at = datetime.utcnow() + timedelta(days=duration_days)

        sub = UserSubscription(
            user_telegram_id=user_id,
            vpn_key_id=key.id,
            product_id=product_id,
            expires_at=expires_at,
            is_active=True,
            is_gift=is_gift,
            gift_from=gift_from,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub


async def get_user_active_subscriptions(user_id: int) -> list:
    async with async_session() as session:
        result = await session.execute(
            select(UserSubscription).where(
                UserSubscription.user_telegram_id == user_id,
                UserSubscription.is_active == True,
                UserSubscription.expires_at > datetime.utcnow()
            )
        )
        return result.scalars().all()


async def get_available_keys_count(product_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(VpnKey.id)).where(
                VpnKey.product_id == product_id,
                VpnKey.is_used == False
            )
        )
        return result.scalar() or 0


async def credit_referral_bonus(referrer_id: int, referred_id: int, bonus_type: str, days: int = 0):
    async with async_session() as session:
        bonus = ReferralBonus(
            referrer_id=referrer_id,
            referred_id=referred_id,
            bonus_type=bonus_type,
            bonus_days=days,
        )
        session.add(bonus)
        user_result = await session.execute(select(User).where(User.telegram_id == referrer_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.bonus_days += days
        await session.commit()


async def credit_partner_bonus(referrer_id: int, referred_id: int, amount: float, percent: float = 0.30):
    bonus_amount = round(amount * percent, 2)
    async with async_session() as session:
        bonus = ReferralBonus(
            referrer_id=referrer_id,
            referred_id=referred_id,
            bonus_type="partner",
            bonus_amount=bonus_amount,
        )
        session.add(bonus)
        user_result = await session.execute(select(User).where(User.telegram_id == referrer_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.partner_balance += bonus_amount
        await session.commit()


async def get_referral_stats(user_id: int) -> dict:
    async with async_session() as session:
        invited_result = await session.execute(
            select(func.count(User.id)).where(User.referred_by == user_id)
        )
        invited = invited_result.scalar() or 0

        bonuses_result = await session.execute(
            select(func.sum(ReferralBonus.bonus_days)).where(
                ReferralBonus.referrer_id == user_id
            )
        )
        total_bonus_days = bonuses_result.scalar() or 0

        user_result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user_result.scalar_one_or_none()
        current_bonus = user.bonus_days if user else 0

        reg_bonuses_result = await session.execute(
            select(func.count(ReferralBonus.id)).where(
                ReferralBonus.referrer_id == user_id,
                ReferralBonus.bonus_type == "registration"
            )
        )
        reg_bonuses = reg_bonuses_result.scalar() or 0

        purchase_bonuses_result = await session.execute(
            select(func.count(ReferralBonus.id)).where(
                ReferralBonus.referrer_id == user_id,
                ReferralBonus.bonus_type == "purchase"
            )
        )
        purchase_bonuses = purchase_bonuses_result.scalar() or 0

        return {
            "invited": invited,
            "total_bonus_days": total_bonus_days,
            "current_bonus": current_bonus,
            "reg_bonuses": reg_bonuses,
            "purchase_bonuses": purchase_bonuses,
        }


async def get_partner_stats(user_id: int) -> dict:
    async with async_session() as session:
        confirmed_result = await session.execute(
            select(func.count(User.id)).where(User.partner_referred_by == user_id)
        )
        confirmed = confirmed_result.scalar() or 0

        buyers_result = await session.execute(
            select(func.count(Payment.id)).where(
                Payment.user_telegram_id.in_(
                    select(User.telegram_id).where(User.partner_referred_by == user_id)
                ),
                Payment.status == "paid"
            )
        )
        buyers = buyers_result.scalar() or 0

        total_credited_result = await session.execute(
            select(func.sum(ReferralBonus.bonus_amount)).where(
                ReferralBonus.referrer_id == user_id,
                ReferralBonus.bonus_type == "partner"
            )
        )
        total_credited = total_credited_result.scalar() or 0.0

        user_result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user_result.scalar_one_or_none()
        available = user.partner_balance if user else 0.0
        withdrawn = user.partner_withdrawn if user else 0.0

        return {
            "confirmed": confirmed,
            "buyers": buyers,
            "total_credited": round(total_credited, 2),
            "withdrawn": round(withdrawn, 2),
            "available": round(available, 2),
        }
