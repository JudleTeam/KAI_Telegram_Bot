import datetime

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks
from tgbot.misc.texts import reply_commands, messages, buttons


async def send_schedule_menu(message: Message):
    _ = message.bot.get('_')
    week_parity = int(datetime.datetime.now().strftime("%V")) % 2
    week_parity = buttons.odd_week if week_parity else buttons.even_week
    await message.answer(_(messages.schedule_menu).format(week=md.hunderline(week_parity)), reply_markup=inline_keyboards.get_main_schedule_keyboard(_))


async def send_profile_menu(message: Message):
    _ = message.bot.get('_')

    await message.answer(_(messages.profile_menu), reply_markup=inline_keyboards.get_profile_keyboard(_))


async def show_profile_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')

    if callback_data['payload'] == 'back_gc':
        await state.finish()

    await call.message.edit_text(_(messages.profile_menu), reply_markup=inline_keyboards.get_profile_keyboard(_))


async def send_shop_menu(message: Message):
    _ = message.bot.get('_')

    await message.answer(_(messages.in_development))


async def send_education_menu(message: Message):
    _ = message.bot.get('_')

    await message.answer(_(messages.in_development))


def register_main_menu(dp: Dispatcher):
    dp.register_message_handler(send_schedule_menu, Text(startswith=reply_commands.schedule_symbol))

    dp.register_message_handler(send_profile_menu, Text(startswith=reply_commands.profile_symbol))
    dp.register_callback_query_handler(show_profile_menu, callbacks.navigation.filter(to='profile'), state='*')

    dp.register_message_handler(send_shop_menu, Text(startswith=reply_commands.shop_symbol))

    dp.register_message_handler(send_education_menu, Text(startswith=reply_commands.education_symbol))