import logging
import os
from pathlib import Path

from aiogram import Router
from aiogram.exceptions import AiogramError
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.utils import markdown as md
from aiogram.utils.i18n import gettext as _
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.config import Config
from tgbot.middlewares.language import CacheAndDatabaseI18nMiddleware
from tgbot.misc.texts import messages
from tgbot.services.database.models import User
from tgbot.services.utils import get_user_description

router = Router()


async def update_user_block_and_notify(message: Message, is_blocked: bool, db: async_sessionmaker, redis: Redis,
                                       config: Config, i18n: CacheAndDatabaseI18nMiddleware):
    args = message.text.split()
    if len(args) != 2:
        await message.answer(_(messages.ban_unban_bad_format).format(command=args[0]))
        return

    user_id_to_update = args[1]
    if not user_id_to_update.isdigit():
        await message.answer(_(messages.ban_unban_bad_format).format(command=args[0]))
        return

    user_id_to_update = int(user_id_to_update)
    if user_id_to_update == message.from_user.id or user_id_to_update in config.bot.main_admins_ids:
        await message.answer(_(messages.dont_do))
        return

    async with db.begin() as session:
        user_to_update = await session.get(User, user_id_to_update)
        if not user_to_update:
            await message.answer(_(messages.user_not_exist).format(user_id=md.hcode(user_id_to_update)))
            return

        user_to_update.is_blocked = is_blocked

    if is_blocked:
        await redis.set(name=f'{user_id_to_update}:blocked', value='', ex=3600)

    logging.info(f'Admin {message.from_user.id} {args[0][1:]} user {user_to_update.telegram_id}')

    user_locale = await i18n.get_user_locale(user_id_to_update, redis, db)
    if is_blocked:
        await message.answer(_(messages.user_has_been_blocked).format(user_id=md.hcode(user_id_to_update)))
        to_user = _(messages.admin_block, locale=user_locale)
    else:
        await message.answer(_(messages.user_has_been_unblocked).format(user_id=md.hcode(user_id_to_update)))
        to_user = _(messages.admin_unblock, locale=user_locale)

    await message.bot.send_message(chat_id=user_to_update.telegram_id, text=to_user)


@router.message(Command('pardon', 'unban', 'unblock'))
async def pardon_user(message: Message, db: async_sessionmaker, redis: Redis, config: Config,
                      i18n_middleware: CacheAndDatabaseI18nMiddleware):
    await update_user_block_and_notify(
        message, is_blocked=False, i18n=i18n_middleware, db=db, redis=redis, config=config
    )


@router.message(Command('ban', 'block'))
async def block_user(message: Message, db: async_sessionmaker, redis: Redis, config: Config,
                     i18n_middleware: CacheAndDatabaseI18nMiddleware):
    await update_user_block_and_notify(
        message, is_blocked=True, i18n=i18n_middleware, db=db, redis=redis, config=config
    )


@router.message(Command('users', 'block'))
async def send_users(message: Message, db: async_sessionmaker):
    all_users = await User.get_all(db)

    formatted_users = list()
    for user in all_users:
        try:
            tg_user = await message.bot.get_chat(user.telegram_id)
        except AiogramError:
            pass
        else:
            user_tag = tg_user.username if tg_user.username else tg_user.full_name
            formatted_users.append(f'{md.hcode(tg_user.id):_<28} {user_tag}')

    await message.answer('\n'.join(formatted_users))
    logging.info(f'Admin {message.from_user.id} used "/users"')


@router.message(Command('set_prefix'))
async def set_prefix(message: Message, db: async_sessionmaker):
    args = message.text.split()
    if len(args) not in (2, 3) or not args[1].isdigit() or (len(args) == 3 and len(args[2]) > 32):
        await message.answer(_(messages.set_prefix_bad_format))
        return

    user_id = args[1]
    prefix = args[2] if len(args) == 3 else None
    async with db.begin() as session:
        user = await session.get(User, int(user_id))
        if not user or not user.kai_user:
            await message.answer(_(messages.set_prefix_bad_user).format(user_id=md.hcode(user_id)))
            return

        user.kai_user.prefix = prefix

    await message.answer(_(messages.prefix_set).format(user_id=md.hcode(user_id), prefix=prefix))


@router.message(Command('last_log'))
async def send_last_log(message: Message, log_file):
    await message.answer_document(FSInputFile(Path(os.getcwd()).joinpath(log_file)))


@router.message(Command('user_info'))
async def send_user_info(message: Message, db: async_sessionmaker):
    args = message.text.split()
    if len(args) != 2:
        await message.answer(_(messages.ban_unban_bad_format).format(command=args[0]))
        return

    user_to_show_id = args[1]
    if not user_to_show_id.isdigit():
        await message.answer(_(messages.ban_unban_bad_format).format(command=args[0]))
        return

    async with db.begin() as session:
        user_to_show = await session.get(User, int(user_to_show_id))
        if not user_to_show:
            await message.answer(_(messages.user_not_exist).format(user_id=md.hcode(user_to_show_id)))
            return

    tg_user = await message.bot.get_chat(user_to_show_id)
    text = get_user_description(_, tg_user, user_to_show, for_admin=True)

    await message.answer(text)


@router.message(Command('send_message'))
async def send_message(message: Message, db: async_sessionmaker):
    args = message.text.split()
    if len(args) != 2 or not message.reply_to_message:
        await message.answer(_(messages.send_message_bad_format))
        return

    user_to_send_id = args[1]
    if not user_to_send_id.isdigit():
        await message.answer(_(messages.send_message_bad_format))
        return

    async with db.begin() as session:
        user_to_send = await session.get(User, int(user_to_send_id))
        if not user_to_send:
            await message.answer(_(messages.user_not_exist).format(user_id=md.hcode(user_to_send_id)))
            return

    await message.reply_to_message.send_copy(chat_id=user_to_send_id)
    await message.reply_to_message.reply(_(messages.message_sent).format(user_id=md.hcode(user_to_send_id)))
