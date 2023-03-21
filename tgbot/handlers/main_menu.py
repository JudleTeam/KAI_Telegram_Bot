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


async def send_schedule_menu(message: Message):
    _ = message.bot.get('_')
    db_session = message.bot.get('database')
    async with db_session() as session:
        user = await session.get(User, message.from_id)
    group_name = user.group.group_name if user.group else '????'
    week_parity = int(datetime.datetime.now().strftime("%V")) % 2
    week_parity = _(buttons.odd_week) if week_parity else _(buttons.even_week)
    await message.answer(_(messages.schedule_menu).format(week=md.hunderline(week_parity)),
                         reply_markup=inline_keyboards.get_main_schedule_keyboard(_, group_name))


async def send_profile_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    db = message.bot.get('database')

    await state.finish()

    async with db() as session:
        user = await session.get(User, message.from_id)

    s_group = md.hcode(user.group.group_name) if user.group else '????'
    roles_str = ', '.join(map(_, user.get_roles_titles_to_show()))

    text = _(messages.profile_menu).format(roles=roles_str, s_group_name=s_group)
    if user.has_role(roles.verified):
        text += '\n\n' + _(messages.verified_info).format(
            full_name=md.hcode(user.kai_user.full_name),
            group_pos=md.hcode(user.kai_user.position),
            n_group_name=md.hcode(user.kai_user.group.group_name),
            phone=md.hcode(user.kai_user.phone or _(messages.missing)),
            email=md.hcode(user.kai_user.email)
        )

    if user.has_role(roles.authorized):
        text += '\n' + _(messages.authorized_info).format(zach=md.hcode(user.kai_user.zach_number))

    await message.answer(text, reply_markup=inline_keyboards.get_profile_keyboard(_))


async def show_profile_menu(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    if callback_data['payload'] == 'back_gc':
        await state.finish()

    async with db() as session:
        user = await session.get(User, call.from_user.id)

    s_group = md.hcode(user.group.group_name) if user.group else '????'
    roles_str = ', '.join(map(_, user.get_roles_titles_to_show()))

    text = _(messages.profile_menu).format(roles=roles_str, s_group_name=s_group)
    if user.has_role(roles.verified):
        text += '\n\n' + _(messages.verified_info).format(
            full_name=md.hcode(user.kai_user.full_name),
            group_pos=md.hcode(user.kai_user.position),
            n_group_name=md.hcode(user.kai_user.group.group_name),
            phone=md.hcode(user.kai_user.phone or _(messages.missing)),
            email=md.hcode(user.kai_user.email)
        )

    if user.has_role(roles.authorized):
        text += '\n' + _(messages.authorized_info).format(zach=md.hcode(user.kai_user.zach_number))

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


def register_main_menu(dp: Dispatcher):
    dp.register_message_handler(send_schedule_menu, Text(startswith=reply_commands.schedule_symbol), state='*')

    dp.register_callback_query_handler(send_main_menu, callbacks.navigation.filter(to='main_menu'),
                                       state=states.GroupChoose.waiting_for_group)

    dp.register_message_handler(send_profile_menu, Text(startswith=reply_commands.profile_symbol), state='*')
    dp.register_callback_query_handler(show_profile_menu, callbacks.navigation.filter(to='profile'), state='*')

    dp.register_message_handler(send_shop_menu, Text(startswith=reply_commands.shop_symbol), state='*')

    dp.register_message_handler(send_education_menu, Text(startswith=reply_commands.education_symbol), state='*')
    dp.register_callback_query_handler(show_education_menu, callbacks.navigation.filter(to='education'))
