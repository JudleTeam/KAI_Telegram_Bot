from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils import markdown as md

from tgbot.handlers.education import show_my_group
from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks, states
from tgbot.misc.texts import messages
from tgbot.services.database.models import User


async def show_classmates(call: CallbackQuery):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    async with db() as session:
        user = await session.get(User, call.from_user.id)

    classmates = await user.kai_user.get_classmates(db)
    formatted_classmates = list()
    for member in classmates:
        name = member.full_name
        if member.telegram_user_id:
            member_tg = await call.bot.get_chat(member.telegram_user_id)
            if member_tg.mention:
                name = md.hlink(member.full_name, f't.me/{member_tg.mention[1:]}')

        prefix = member.prefix or ''

        formatted_member = f'{member.position}. {prefix} {name}'
        formatted_classmates.append(formatted_member)

    classmates_str = '\n'.join(formatted_classmates)

    await call.message.edit_text(
        _(messages.classmates_list).format(
            group_name=md.hcode(user.kai_user.group.group_name),
            classmates=classmates_str
        ),
        reply_markup=inline_keyboards.get_back_keyboard(_, 'my_group'),
        disable_web_page_preview=True
    )
    await call.answer()


async def start_group_pip_text_input(call: CallbackQuery, state: FSMContext):
    _ = call.bot.get('_')

    await call.message.edit_text(_(messages.pin_text_input), reply_markup=inline_keyboards.get_pin_text_keyboard(_))

    await states.GroupPinText.waiting_for_text.set()
    await state.update_data(main_call=call.to_python())
    await call.answer()


async def get_group_pin_text(message: Message, state: FSMContext):
    db = message.bot.get('database')

    await message.delete()
    async with db.begin() as session:
        user = await session.get(User, message.from_user.id)
        user.kai_user.group.pinned_text = message.text

    async with state.proxy() as data:
        call = CallbackQuery(**data['main_call'])

    await state.finish()
    await show_my_group(call)


async def clear_pin_text(call: CallbackQuery, state: FSMContext):
    db = call.bot.get('database')

    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.kai_user.group.pinned_text = None

    await state.finish()
    await show_my_group(call)


def register_my_group(dp: Dispatcher):
    dp.register_callback_query_handler(show_classmates, callbacks.navigation.filter(to='classmates'))
    dp.register_callback_query_handler(start_group_pip_text_input, callbacks.navigation.filter(to='edit_pin_text'))
    dp.register_message_handler(get_group_pin_text, state=states.GroupPinText.waiting_for_text)
    dp.register_callback_query_handler(clear_pin_text, callbacks.navigation.filter(to='clear_pin_text'),
                                       state=states.GroupPinText.waiting_for_text)
