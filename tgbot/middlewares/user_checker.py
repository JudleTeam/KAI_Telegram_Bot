import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.event.bases import skip, CancelHandler
from aiogram.types import ContentType, TelegramObject, CallbackQuery
from aiogram.utils.i18n import gettext as _
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.services.database.models import User
from tgbot.misc.texts import messages


class UserCheckerMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        if isinstance(event, CallbackQuery):
            if 'start' in event.data:
                return await handler(event, data)

            message = event.message
        else:
            message = event

        db_session: async_sessionmaker = data.get('db')
        redis: Redis = data.get('redis')
        bot: Bot = data.get('bot')

        if message.chat.type != 'private' and message.content_type == ContentType.NEW_CHAT_MEMBERS:
            if any(bot.id == new_member.id for new_member in message.new_chat_members):
                await message.answer(_(messages.group_chat_error))
            raise CancelHandler

        database_user = None
        cached_is_user_exists = await redis.exists(f'{message.chat.id}:exists')
        if not cached_is_user_exists:
            async with db_session() as session:
                database_user = await session.get(User, message.chat.id)

            if database_user is None:
                if message.text == '/start':
                    return await handler(event, data)

                logging.error(f'[{message.chat.id}]: Unregistered')
                await message.answer(messages.user_unregistered)
                raise CancelHandler

            await redis.set(name=f'{message.chat.id}:exists', value='', ex=3600)

        cached_is_user_blocked = await redis.exists(f'{message.chat.id}:blocked')
        if cached_is_user_blocked:
            await message.answer(_(messages.user_blocked))
            raise CancelHandler

        if database_user is None:
            async with db_session() as session:
                database_user = await session.get(User, message.chat.id)

        if database_user is None:
            if message.text == '/start':
                return await handler(event, data)

            logging.error(f'[{message.chat.id}]: Unregistered')
            await message.answer(messages.user_unregistered)
            raise CancelHandler

        if database_user.is_blocked:
            await redis.set(name=f'{message.chat.id}:blocked', value='', ex=3600)
            await message.answer(_(messages.user_blocked))
            raise CancelHandler

        return await handler(event, data)
