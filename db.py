from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.database.models import Base
from bot.config import DB_PATH

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_settings()


async def _seed_settings():
    from bot.database.db import async_session
    from bot.database.models import BotSettings
    from sqlalchemy import select

    defaults = {
        "trial_hours": "24",
        "support_link": "",
        "channel_link": "",
        "instruction_text": (
            "📱 <b>Как добавить ключ в приложение Happ:</b>\n\n"
            "1. Скачайте приложение <b>Happ</b> из App Store или Google Play\n"
            "2. Откройте приложение и нажмите <b>+</b> (добавить)\n"
            "3. Вставьте ваш ключ в поле ввода\n"
            "4. Нажмите <b>Подключиться</b>\n"
            "5. Готово! VPN активирован ✅"
        ),
        "min_withdrawal": "500",
        "withdrawal_enabled": "1",
        "welcome_text": "👋 Добро пожаловать! Выберите раздел:",
        "main_photo_file_id": "",
        "shop_photo_file_id": "",
        "referral_photo_file_id": "",
    }

    async with async_session() as session:
        for key, value in defaults.items():
            result = await session.execute(select(BotSettings).where(BotSettings.key == key))
            existing = result.scalar_one_or_none()
            if not existing:
                session.add(BotSettings(key=key, value=value))
        await session.commit()


async def get_setting(key: str, default: str = "") -> str:
    from bot.database.models import BotSettings
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(BotSettings).where(BotSettings.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else default


async def set_setting(key: str, value: str):
    from bot.database.models import BotSettings
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(BotSettings).where(BotSettings.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            session.add(BotSettings(key=key, value=value))
        await session.commit()
