import logging

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message

from tgbot.misc import callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import User


async def update_user_block_and_notify(message: Message, is_blocked: bool, blocked_msg: str, unblocked_msg: str):
    _ = message.bot.get('_')
    db_session = message.bot.get('database')
    redis = message.bot.get('redis')

    args = message.text.split()
    if len(args) != 2:
        await message.answer(_(messages.ban_unban_invalid_format.format(command=args[0])))
        return

    user_id_to_update = args[1]
    if not user_id_to_update.isdigit():
        await message.answer(_(messages.ban_unban_invalid_format.format(command=args[0])))
        return

    if int(user_id_to_update) == message.from_user.id:
        await message.answer(_(messages.dont_do))
        return

    async with db_session.begin() as session:
        user_to_update = await session.get(User, int(user_id_to_update))
        if not user_to_update:
            await message.answer(_(messages.user_not_exist.format(user_id=user_id_to_update)))
            return

        user_to_update.is_blocked = is_blocked

    redis_value = '1' if is_blocked else ''
    await redis.set(name=f'{user_id_to_update}:blocked', value=redis_value)
    logging.info(f'Admin {message.from_id} {args[0][1:]} user {user_to_update.telegram_id}')

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
        formatted_users.append(f'[{tg_user.id}] {user_tag}')

    await message.answer('\n'.join(formatted_users))
    logging.info(f'Admin {message.from_id} used "/users"')


def register_admin_commands(dp: Dispatcher):
    dp.register_message_handler(block_user, commands=['ban'], is_admin=True)
    dp.register_message_handler(pardon_user, commands=['pardon'], is_admin=True)
    dp.register_message_handler(send_users, commands=['users'], is_admin=True)
