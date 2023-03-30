import logging
import os
from pathlib import Path

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message, InputFile
from aiogram.utils import markdown as md

from tgbot.misc import callbacks
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User


async def update_user_block_and_notify(message: Message, is_blocked: bool, blocked_msg: str, unblocked_msg: str):
    _ = message.bot.get('_')
    db_session = message.bot.get('database')
    redis = message.bot.get('redis')
    config = message.bot.get('config')

    args = message.text.split()
    if len(args) != 2:
        await message.answer(_(messages.ban_unban_bad_format.format(command=args[0])))
        return

    user_id_to_update = args[1]
    if not user_id_to_update.isdigit():
        await message.answer(_(messages.ban_unban_bad_format.format(command=args[0])))
        return

    user_id_to_update = int(user_id_to_update)
    if user_id_to_update == message.from_user.id or user_id_to_update in config.bot.main_admins_ids:
        await message.answer(_(messages.dont_do))
        return

    async with db_session.begin() as session:
        user_to_update = await session.get(User, user_id_to_update)
        if not user_to_update:
            await message.answer(_(messages.user_not_exist.format(user_id=md.hcode(user_id_to_update))))
            return

        user_to_update.is_blocked = is_blocked

    redis_value = '1' if is_blocked else ''
    await redis.set(name=f'{user_id_to_update}:blocked', value=redis_value)
    logging.info(f'Admin {message.from_id} {args[0][1:]} user {user_to_update.telegram_id}')

    if is_blocked:
        await message.answer(_(messages.user_has_been_blocked).format(user_id=md.hcode(user_id_to_update)))
    else:
        await message.answer(_(messages.user_has_been_unblocked).format(user_id=md.hcode(user_id_to_update)))

    user_locale = user_to_update.language.code if user_to_update.language else 'en'
    await message.bot.send_message(
        chat_id=user_to_update.telegram_id,
        text=_(blocked_msg, locale=user_locale) if is_blocked else _(unblocked_msg, locale=user_locale),
    )


async def pardon_user(message: Message):
    await update_user_block_and_notify(
        message,
        is_blocked=False,
        blocked_msg=messages.admin_unblock,
        unblocked_msg=messages.user_has_been_unblocked
    )


async def block_user(message: Message):
    await update_user_block_and_notify(
        message,
        is_blocked=True,
        blocked_msg=messages.admin_block,
        unblocked_msg=messages.user_has_been_blocked
    )


async def send_users(message: Message):
    db_session = message.bot.get('database')

    all_users = await User.get_all(db_session)

    formatted_users = list()
    for user in all_users:
        tg_user = await message.bot.get_chat(user.telegram_id)
        user_tag = tg_user.mention if tg_user.mention else tg_user.full_name
        formatted_users.append(f'{md.hcode(tg_user.id):_<28} {user_tag}')

    await message.answer('\n'.join(formatted_users))
    logging.info(f'Admin {message.from_id} used "/users"')


async def set_prefix(message: Message):
    _ = message.bot.get('_')
    db = message.bot.get('database')

    args = message.text.split()
    if len(args) != 3 or len(args[1]) > 32 or not args[2].isdigit():
        await message.answer(_(messages.set_prefix_bad_format))
        return

    prefix = args[1]
    user_id = args[2]
    async with db.begin() as session:
        user = await session.get(User, int(user_id))
        if not user or not user.kai_user:
            await message.answer(_(messages.set_prefix_bad_user).format(user_id=md.hcode(user_id)))
            return

        user.kai_user.prefix = prefix

    await message.answer(_(messages.prefix_set).format(user_id=md.hcode(user_id), prefix=prefix))


async def send_last_log(message: Message):
    await message.answer_document(InputFile(Path(os.getcwd()).joinpath(message.bot.get('log_file'))))


async def send_user_info(message: Message):
    _ = message.bot.get('_')
    db = message.bot.get('database')

    args = message.text.split()
    if len(args) != 2:
        await message.answer(_(messages.ban_unban_bad_format.format(command=args[0])))
        return

    user_to_show_id = args[1]
    if not user_to_show_id.isdigit():
        await message.answer(_(messages.ban_unban_bad_format.format(command=args[0])))
        return

    async with db.begin() as session:
        user_to_show = await session.get(User, int(user_to_show_id))
        if not user_to_show:
            await message.answer(_(messages.user_not_exist.format(user_id=md.hcode(user_to_show_id))))
            return

    s_group = md.hcode(user_to_show.group.group_name) if user_to_show.group else '????'
    roles_str = ', '.join(map(_, user_to_show.get_roles_titles(to_show=False)))

    tg_user = await message.bot.get_chat(user_to_show_id)
    text = _(messages.for_admin_info).format(
        roles=roles_str,
        s_group_name=s_group,
        is_blocked=user_to_show.is_blocked,
        telegram_id=md.hcode(user_to_show_id),
        tg_full_name=md.hcode(tg_user.full_name),
        tg_mention=md.hcode(tg_user.mention),
        telegram_phone=md.hcode(user_to_show.phone)
    )
    if user_to_show.has_role(roles.verified):
        text += '\n' + _(messages.verified_info).format(
            full_name=md.hcode(user_to_show.kai_user.full_name),
            group_pos=md.hcode(user_to_show.kai_user.position),
            n_group_name=md.hcode(user_to_show.kai_user.group.group_name),
            phone=md.hcode(user_to_show.kai_user.phone or _(messages.missing)),
            email=md.hcode(user_to_show.kai_user.email)
        )

    if user_to_show.has_role(roles.authorized):
        text += '\n' + _(messages.authorized_info).format(zach=md.hcode(user_to_show.kai_user.zach_number))

    await message.answer(text)


def register_admin_commands(dp: Dispatcher):
    dp.register_message_handler(block_user, commands=['ban', 'block'], is_admin=True)
    dp.register_message_handler(pardon_user, commands=['pardon', 'unban', 'unblock'], is_admin=True)
    dp.register_message_handler(send_users, commands=['users'], is_admin=True)
    dp.register_message_handler(set_prefix, commands=['set_prefix'], is_admin=True)
    dp.register_message_handler(send_last_log, commands=['last_log'], is_admin=True)
    dp.register_message_handler(send_user_info, commands=['user_info'], is_admin=True)
