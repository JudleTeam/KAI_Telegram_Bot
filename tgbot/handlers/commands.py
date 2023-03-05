import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User, Role


async def command_start(message: Message):
    db = message.bot.get('database')
    _ = message.bot.get('_')

    async with db.begin() as session:
        user = await session.get(User, message.from_id)
        if not user:
            redis = message.bot.get('redis')
            roles_dict = await Role.get_roles_dict(db)
            user = User(telegram_id=message.from_id, roles=[roles_dict[roles.student]])
            session.add(user)

            await redis.set(name=f'{message.from_id}:exists', value='1')
            await message.answer(_(messages.welcome), reply_markup=inline_keyboards.get_start_keyboard(_))
            logging.info(f'New user: {message.from_user.mention} {message.from_user.full_name} [{message.from_id}]')
        else:
            await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))


async def command_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')

    await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))
    await state.finish()


def register_commands(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(command_menu, commands=['menu'], state='*')
