import datetime

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc import callbacks, states
from tgbot.misc.texts import reply_commands, messages, buttons, roles
from tgbot.services.database.models import User
from tgbot.services.utils import get_user_description


async def send_schedule_menu(message: Message):
    _ = message.bot.get('_')
    db_session = message.bot.get('database')
    async with db_session() as session:
        user = await session.get(User, message.from_id)
    group_name = user.group.group_name if user.group else '????'
    week_parity = int(datetime.datetime.now().strftime("%V")) % 2
    week_parity = _(buttons.odd_week) if week_parity else _(buttons.even_week)
    msg = _(messages.schedule_menu).format(
        week=md.hunderline(week_parity),
    )
    await message.answer(msg, reply_markup=inline_keyboards.get_main_schedule_keyboard(_, group_name))


async def send_profile_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    db = message.bot.get('database')

    await state.finish()

    async with db() as session:
        user = await session.get(User, message.from_id)

    text = get_user_description(_, message.from_user, user)

    await message.answer(text, reply_markup=inline_keyboards.get_profile_keyboard(_))


async def show_profile_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    if callback_data['payload'] == 'back_gc':
        await state.finish()

    async with db() as session:
        user = await session.get(User, call.from_user.id)

    text = get_user_description(_, call.from_user, user)

    await call.message.edit_text(text, reply_markup=inline_keyboards.get_profile_keyboard(_))


async def send_shop_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')

    await state.finish()
    await message.answer(_(messages.in_development))


async def show_education_menu(call: CallbackQuery):
    _ = call.bot.get('_')

    await call.message.edit_text(_(messages.education_menu), reply_markup=inline_keyboards.get_education_keyboard(_))


async def send_education_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')

    await state.finish()
    await message.answer(_(messages.education_menu), reply_markup=inline_keyboards.get_education_keyboard(_))


async def send_main_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')

    await call.message.delete()
    if callback_data['payload'] == 'at_start':
        config = call.bot.get('config')
        await call.message.answer(_(messages.channel_advertising),
                                  reply_markup=inline_keyboards.get_channel_keyboard(_, config.misc.channel_link))

    await call.message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))
    await call.answer()
    await state.finish()


async def send_help_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    config = message.bot.get('config')

    await state.finish()
    await message.answer(_(messages.help_menu),
                         reply_markup=inline_keyboards.get_help_keyboard(_, config.misc.contact_link))


def register_main_menu(dp: Dispatcher):
    dp.register_message_handler(send_schedule_menu, Text(startswith=reply_commands.schedule_symbol), state='*')

    dp.register_callback_query_handler(send_main_menu, callbacks.navigation.filter(to='main_menu'), state='*')

    dp.register_message_handler(send_profile_menu, Text(startswith=reply_commands.profile_symbol), state='*')
    dp.register_callback_query_handler(show_profile_menu, callbacks.navigation.filter(to='profile'), state='*')

    dp.register_message_handler(send_shop_menu, Text(startswith=reply_commands.shop_symbol), state='*')

    dp.register_message_handler(send_education_menu, Text(startswith=reply_commands.education_symbol), state='*')
    dp.register_callback_query_handler(show_education_menu, callbacks.navigation.filter(to='education'), state='*')

    dp.register_message_handler(send_help_menu, Text(startswith=reply_commands.help_symbol), state='*')
