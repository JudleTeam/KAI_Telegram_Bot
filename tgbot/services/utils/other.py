import asyncio
import logging
from typing import Sequence

import phonenumbers
from aiogram import Bot
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.utils.exceptions import RetryAfter, BotBlocked, ChatNotFound, UserDeactivated, TelegramAPIError
from phonenumbers import NumberParseException
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.services.database.models import User
from tgbot.services.database.utils import get_user_locale


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


async def send_message(bot: Bot, chat_id: int, text: str, **kwargs) -> None:
    try:
        await bot.send_message(chat_id, text, **kwargs)

    except RetryAfter as error:
        await asyncio.sleep(error.timeout)
        await send_message(bot, chat_id, text)

    except TelegramAPIError as error:
        logging.error(f'[{chat_id}] Something went wrong with TelegramAPI: {error}')

    except Exception as error:
        logging.error(f'[{chat_id}] Something went wrong: {error}')


async def broadcast_text(
        _: I18nMiddleware,
        chats: Sequence[int],
        text: str,
        bot: Bot,
        db: async_sessionmaker,
        format_kwargs: dict = None,
        timeout: float = 0.05,
        **kwargs):

    logging.info('Start broadcasting')

    async with db() as session:
        for chat_id in chats:
            user_locale = await get_user_locale(session, chat_id)
            text_to_send = _.gettext(text, locale=user_locale).format(**format_kwargs)
            await send_message(bot, chat_id, text_to_send, **kwargs)

            await asyncio.sleep(timeout)

    logging.info('Broadcast completed')
