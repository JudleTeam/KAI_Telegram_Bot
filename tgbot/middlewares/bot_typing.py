import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.event.bases import skip
from aiogram.enums import ChatAction
from aiogram.types import ContentType, TelegramObject, CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.services.database.models import User
from tgbot.misc.texts import messages


class BotTypingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: Message,
                       data: Dict[str, Any]) -> Any:
        bot: Bot = data.get('bot')
        if bot is not None:
            await bot.send_chat_action(chat_id=event.from_user.id, action=ChatAction.TYPING)

        return await handler(event, data)
