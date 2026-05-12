from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    referred_by = Column(BigInteger, nullable=True)
    partner_referred_by = Column(BigInteger, nullable=True)
    bonus_days = Column(Integer, default=0)
    partner_balance = Column(Float, default=0.0)
    partner_withdrawn = Column(Float, default=0.0)
    op_verified = Column(Boolean, default=False)
    trial_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscriptions = relationship("UserSubscription", back_populates="user", foreign_keys="UserSubscription.user_telegram_id")
    tickets = relationship("SupportTicket", back_populates="user")


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    channel_id = Column(String, unique=True)
    title = Column(String)
    invite_link = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    duration_days = Column(Integer)
    price_rub = Column(Float)
    price_stars = Column(Integer)
    photo_file_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    keys = relationship("VpnKey", back_populates="product")


class VpnKey(Base):
    __tablename__ = "vpn_keys"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    key_value = Column(Text)
    key_link = Column(String, nullable=True)
    is_used = Column(Boolean, default=False)
    product = relationship("Product", back_populates="keys")
    subscription = relationship("UserSubscription", back_populates="vpn_key", uselist=False)


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    vpn_key_id = Column(Integer, ForeignKey("vpn_keys.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_gift = Column(Boolean, default=False)
    gift_from = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="subscriptions", foreign_keys=[user_telegram_id])
    vpn_key = relationship("VpnKey", back_populates="subscription")
    product = relationship("Product")


class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    duration_days = Column(Integer, nullable=True)
    discount_percent = Column(Integer, default=0)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product")


class UserPromoCode(Base):
    __tablename__ = "user_promo_codes"
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    is_used = Column(Boolean, default=False)
    gifted_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    promo_code = relationship("PromoCode")
    product = relationship("Product")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    amount_rub = Column(Float, nullable=True)
    amount_stars = Column(Integer, nullable=True)
    payment_method = Column(String)
    payment_id = Column(String, nullable=True)
    status = Column(String, default="pending")
    recipient_telegram_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    subject = Column(String)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"))
    sender_id = Column(BigInteger)
    is_admin = Column(Boolean, default=False)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    ticket = relationship("SupportTicket", back_populates="messages")


class BotSettings(Base):
    __tablename__ = "bot_settings"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(Text)


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    amount = Column(Float)
    details = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    referred_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    bonus_type = Column(String)
    bonus_days = Column(Integer, default=0)
    bonus_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
