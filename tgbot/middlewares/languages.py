import logging
from typing import Tuple, Any, Optional

from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler

from tgbot.keyboards import inline_keyboards
from tgbot.misc.texts import messages
from tgbot.services.database.models import User


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> Optional[str]:
        telegram_user = types.User.get_current()

        db_session = telegram_user.bot.get('database')
        redis = telegram_user.bot.get('redis')

        cached_lang = await redis.get(name=f'{telegram_user.id}:lang')

        default_lang = 'en'
        lang = 'en'
        if cached_lang:
            lang = cached_lang.decode()
        else:
            async with db_session() as session:
                database_user = await session.get(User, telegram_user.id)

            if database_user:
                lang = database_user.language.code if database_user.language else default_lang

            await redis.set(name=f'{telegram_user.id}:lang', value=lang, ex=3600)

        if lang not in self.available_locales:
            logging.error(f'[{telegram_user.id}]: Language {lang} no more available')
            await telegram_user.bot.send_message(
                chat_id=telegram_user.id,
                text=messages.language_not_available,
                reply_markup=inline_keyboards.get_start_keyboard(messages._)
            )
            raise CancelHandler()

        return lang
