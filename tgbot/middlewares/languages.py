from typing import Tuple, Any, Optional

from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from tgbot.services.database.models import User


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> Optional[str]:
        telegram_user = types.User.get_current()

        db_session = telegram_user.bot.get('database')
        redis = telegram_user.bot.get('redis')

        cached_lang = await redis.get(name=f'{telegram_user.id}:lang')
        if cached_lang: return cached_lang

        async with db_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_user.id).options(selectinload(User.language))
            database_user = (await session.execute(stmt)).scalar()

        if database_user:
            lang = database_user.language.code
        else:
            lang = 'en'

        await redis.set(name=f'{telegram_user.id}:lang', value=lang)
        return lang
