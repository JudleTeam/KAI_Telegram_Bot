import asyncio
import logging
from typing import Sequence

import phonenumbers
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError
from aiogram.utils.i18n import gettext
from phonenumbers import NumberParseException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.middlewares.language import CacheAndDatabaseI18nMiddleware
from tgbot.services.database.models import User


def parse_phone_number(phone_number) -> str | None:
    """
    Parsing a phone number with an attempt to replace the first 8 with 7 and add 7 if it is not there, on error

    :param phone_number:
    :return: String phone number in E164 format or None if number is not vaild
    """
    phone_number = str(phone_number)
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    try:
        parsed_number = phonenumbers.parse(phone_number)
    except NumberParseException:
        phone_number = phone_number.replace('8', '7', 1)
        try:
            parsed_number = phonenumbers.parse(phone_number)
        except NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed_number):
        phone_number = phone_number.replace('+', '+7')
        try:
            parsed_number = phonenumbers.parse(phone_number)
        except NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed_number):
        return None

    return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)


async def send_message(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    try:
        await bot.send_message(chat_id, text, **kwargs)

    except TelegramRetryAfter as error:
        await asyncio.sleep(error.retry_after)
        return await send_message(bot, chat_id, text)

    except TelegramAPIError as error:
        logging.error(f'[{chat_id}] Something went wrong with TelegramAPI: {error}')

    except Exception as error:
        logging.error(f'[{chat_id}] Something went wrong: {error}')

    else:
        return True

    return False


async def broadcast_text(
        chats: Sequence[int],
        text: str,
        i18n: CacheAndDatabaseI18nMiddleware,
        bot: Bot,
        redis: Redis,
        db: async_sessionmaker,
        format_kwargs: dict = None,
        timeout: float = 0.05,
        **kwargs):
    if format_kwargs is None:
        format_kwargs = {}

    logging.info('Start broadcasting')

    total = len(chats)
    for num, chat_id in enumerate(chats, start=1):
        user_locale = await i18n.get_user_locale(chat_id, redis, db)
        text_to_send = gettext(text, locale=user_locale).format(**format_kwargs)
        result = await send_message(bot, chat_id, text_to_send, **kwargs)

        if result:
            logging.info(f'[{num} / {total}] Message has been sent to {chat_id}')
        else:
            logging.info(f'[{num} / {total}] Message was not sent to {chat_id}')

        await asyncio.sleep(timeout)

    logging.info('Broadcast completed')
