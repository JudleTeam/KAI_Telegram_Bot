import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils import markdown as md
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.config import Config
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc.callbacks import Navigation
from tgbot.misc.texts import reply_commands, messages, buttons
from tgbot.services.database.models import User
from tgbot.services.utils import get_user_description

router = Router()


@router.message(F.text.startswith(reply_commands.schedule_symbol))
async def send_schedule_menu(message: Message, _, db: async_sessionmaker):
    async with db() as session:
        user = await session.get(User, message.from_id)
    group_name = user.group.group_name if user.group else '????'
    week_parity = int(datetime.datetime.now().strftime("%V")) % 2
    week_parity = _(buttons.odd_week) if week_parity else _(buttons.even_week)
    msg = _(messages.schedule_menu).format(
        week=md.hunderline(week_parity),
    )
    if user.use_emoji:
        msg += _(messages.emoji_hint)
    await message.answer(msg, reply_markup=inline_keyboards.get_main_schedule_keyboard(_, group_name))


@router.message(F.text.startswith(reply_commands.profile_symbol))
async def send_profile_menu(message: Message, state: FSMContext, _, db: async_sessionmaker):
    await state.clear()

    async with db() as session:
        user = await session.get(User, message.from_id)

    text = get_user_description(_, message.from_user, user)

    await message.answer(text, reply_markup=inline_keyboards.get_profile_keyboard(_))


@router.callback_query(Navigation.filter(F.to == Navigation.To.profile))
async def show_profile_menu(call: CallbackQuery, callback_data: Navigation, state: FSMContext, _, db: async_sessionmaker):
    if callback_data.payload == 'back_gc':
        await state.clear()

    async with db() as session:
        user = await session.get(User, call.from_user.id)

    text = get_user_description(_, call.from_user, user)

    await call.message.edit_text(text, reply_markup=inline_keyboards.get_profile_keyboard(_))


@router.message(F.text.startswith(reply_commands.shop_symbol))
async def send_shop_menu(message: Message, state: FSMContext, _):
    await state.clear()
    await message.answer(_(messages.in_development))


@router.callback_query(Navigation.filter(F.to == Navigation.To.education))
async def show_education_menu(call: CallbackQuery, _):
    await call.message.edit_text(_(messages.education_menu), reply_markup=inline_keyboards.get_education_keyboard(_))


@router.message(F.text.startswith(reply_commands.education_symbol))
async def send_education_menu(message: Message, state: FSMContext, _):
    await state.clear()
    await message.answer(_(messages.education_menu), reply_markup=inline_keyboards.get_education_keyboard(_))


@router.callback_query(Navigation.filter(F.action == Navigation.To.main_menu))
async def send_main_menu(call: CallbackQuery, callback_data: dict, state: FSMContext, _, config: Config):
    await call.message.delete()
    if callback_data['payload'] == 'at_start':
        await call.message.answer(_(messages.channel_advertising),
                                  reply_markup=inline_keyboards.get_channel_keyboard(_, config.misc.channel_link))

    await call.message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))
    await state.clear()
    await call.answer()


@router.message(F.text.startswith(reply_commands.help_symbol))
async def send_help_menu(message: Message, state: FSMContext, _, config: Config):
    await state.clear()
    keyboard = inline_keyboards.get_help_keyboard(
        _, config.misc.contact_link, config.misc.channel_link, config.misc.donate_link, config.misc.guide_link
    )
    await message.answer(_(messages.help_menu), reply_markup=keyboard)
