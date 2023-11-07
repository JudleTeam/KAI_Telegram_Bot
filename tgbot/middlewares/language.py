import logging
from typing import Dict, Any, Optional

from aiogram import Bot
from aiogram.types import TelegramObject, User
from aiogram.utils.i18n import I18nMiddleware, I18n
from iso_language_codes import language_autonym
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.keyboards import reply_keyboards
from tgbot.misc.texts import messages
from tgbot.services.database.models import User as TelegramUser


class CacheAndDatabaseI18nMiddleware(I18nMiddleware):
    def __init__(
            self,
            i18n: I18n,
            i18n_key: Optional[str] = "i18n",
            middleware_key: str = "i18n_middleware",
            locale_cache_time: int = 3600
    ) -> None:
        super().__init__(i18n=i18n, i18n_key=i18n_key, middleware_key=middleware_key)
        self.locale_cache_time = locale_cache_time

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        event_from_user: Optional[User] = data.get("event_from_user", None)

        if event_from_user is None:
            return self.i18n.default_locale

        redis: Redis = data.get('redis')
        redis_key = f'{event_from_user.id}:lang'

        cached_locale = await redis.get(redis_key)
        if cached_locale is not None:
            return cached_locale.decode()

        db: async_sessionmaker = data.get('db')
        async with db() as session:
            db_user = await session.get(TelegramUser, event_from_user.id)

        if db_user is None and not event_from_user.language_code:
            return self.i18n.default_locale

        if db_user and db_user.language in self.i18n.available_locales:
            await redis.set(name=redis_key, value=db_user.language, ex=self.locale_cache_time)
            return db_user.language

        if event_from_user.language_code and event_from_user.language_code in self.i18n.available_locales:
            new_locale = event_from_user.language_code
        else:
            new_locale = self.i18n.default_locale

        await self.set_locale(event_from_user.id, new_locale, redis, db)

        bot: Bot = data.get('bot')
        try:
            text = self.i18n.gettext(
                messages.language_not_available, locale=new_locale
            ).format(language=language_autonym(new_locale))
            await bot.send_message(
                chat_id=event_from_user.id,
                text=text,
                reply_markup=reply_keyboards.get_main_keyboard()
            )
        except Exception as e:
            logging.error(f'[{event_from_user.id}] Error during sending language error message: {e}')

        return new_locale

    async def set_locale(self, user_id: int, locale: str, redis: Redis, db: async_sessionmaker) -> None:
        self.i18n.current_locale = locale
        async with db.begin() as session:
            db_user = await session.get(TelegramUser, user_id)
            if db_user is not None:
                db_user.language = locale
        await redis.set(name=f'{user_id}:lang', value=locale, ex=self.locale_cache_time)

    async def get_user_locale(self, user_id: int, redis: Redis, db: async_sessionmaker) -> str:
        cached_locale = await redis.get(f'{user_id}:lang')
        if cached_locale is not None:
            return cached_locale.decode()

        async with db() as session:
            db_user = await session.get(TelegramUser, user_id)

        if db_user is None:
            return self.i18n.default_locale

        if db_user.language in self.i18n.available_locales:
            return db_user.language

        return self.i18n.default_locale
