from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message

from tgbot.misc import callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import User


async def update_user_block(message: Message, is_blocked: bool) -> User | None:
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

    async with db_session.begin() as session:
        user_to_update = await session.get(User, int(user_id_to_update))
        if not user_to_update:
            await message.answer(_(messages.user_not_exist.format(user_id=user_id_to_update)))
            return

        user_to_update.is_blocked = is_blocked

    redis_value = '1' if is_blocked else ''
    await redis.set(name=f'{user_id_to_update}:blocked', value=redis_value)

    return user_to_update


async def pardon_user(message: Message):
    _ = message.bot.get('_')

    user_to_pardon = await update_user_block(message, False)
    if user_to_pardon is None:
        return

    await message.bot.send_message(
        chat_id=user_to_pardon.telegram_id,
        text=_(messages.admin_unblock, locale=user_to_pardon.language.code)
    )
    await message.answer(_(messages.user_has_been_unblocked.format(user_id=user_to_pardon.telegram_id)))


async def block_user(message: Message):
    _ = message.bot.get('_')

    user_to_block = await update_user_block(message, True)
    if user_to_block is None:
        return

    await message.bot.send_message(
        chat_id=user_to_block.telegram_id,
        text=_(messages.admin_block, locale=user_to_block.language.code)
    )
    await message.answer(_(messages.user_has_been_blocked.format(user_id=user_to_block.telegram_id)))


async def send_users(message: Message):
    db_session = message.bot.get('database')

    all_users = await User.get_all(db_session)

    formatted_users = list()
    for user in all_users:
        tg_user = await message.bot.get_chat(user.telegram_id)
        user_tag = tg_user.mention if tg_user.mention else tg_user.full_name
        formatted_users.append(f'[{tg_user.id}] {user_tag}')

    await message.answer('\n'.join(formatted_users))


def register_admin_commands(dp: Dispatcher):
    dp.register_message_handler(block_user, commands=['ban'], is_admin=True)
    dp.register_message_handler(pardon_user, commands=['pardon'], is_admin=True)
    dp.register_message_handler(send_users, commands=['users'], is_admin=True)
