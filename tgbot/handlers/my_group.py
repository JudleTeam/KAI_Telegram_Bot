from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile
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
            link = f't.me/{member_tg.username}' if member_tg.username else member_tg.user_url
            name = md.hlink(member.full_name, link)

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


async def show_documents(call: CallbackQuery):
    _ = call.bot.get('_')

    await call.message.edit_text(_(messages.documents), reply_markup=inline_keyboards.get_documents_keyboard(_))
    await call.answer()


async def send_document(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    _ = call.bot.get('_')

    async with db() as session:
        user = await session.get(User, call.from_user.id)

    match callback_data['payload']:
        case 'syllabus': file_url = user.kai_user.group.syllabus
        case 'program': file_url = user.kai_user.group.educational_program
        case 'schedule': file_url = user.kai_user.group.study_schedule
        case _:
            await call.answer(_(messages.base_error), show_alert=True)
            return

    await call.message.answer_document(InputFile.from_url(file_url))
    await call.answer()


def register_my_group(dp: Dispatcher):
    dp.register_callback_query_handler(show_classmates, callbacks.navigation.filter(to='classmates'))
    dp.register_callback_query_handler(start_group_pip_text_input, callbacks.navigation.filter(to='edit_pin_text'))
    dp.register_message_handler(get_group_pin_text, state=states.GroupPinText.waiting_for_text)
    dp.register_callback_query_handler(clear_pin_text, callbacks.action.filter(name='clear_pin_text'),
                                       state=states.GroupPinText.waiting_for_text)
    dp.register_callback_query_handler(show_documents, callbacks.navigation.filter(to='documents'))
    dp.register_callback_query_handler(send_document, callbacks.action.filter(name='doc'))
