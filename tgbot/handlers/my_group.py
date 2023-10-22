from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.utils import markdown as md
from aiogram.utils.i18n import gettext as _
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.education import show_my_group
from tgbot.keyboards import inline_keyboards
from tgbot.misc import states
from tgbot.misc.callbacks import Action, Navigation
from tgbot.misc.texts import messages, buttons
from tgbot.services.database.models import User

router = Router()


@router.callback_query(Navigation.filter(F.to == Navigation.To.classmates))
async def show_classmates(call: CallbackQuery, db: async_sessionmaker):
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
        reply_markup=inline_keyboards.get_back_keyboard(Navigation.To.my_group),
        disable_web_page_preview=True
    )
    await call.answer()


@router.callback_query(Action.filter(F.name == Action.Name.edit_pinned_text))
async def start_group_pip_text_input(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(_(messages.pin_text_input), reply_markup=inline_keyboards.get_pin_text_keyboard())

    await state.set_state(states.GroupPinText.waiting_for_text)
    await state.update_data(main_call=call.to_python())
    await call.answer()


@router.message(states.GroupPinText.waiting_for_text)
async def get_group_pin_text(message: Message, state: FSMContext, db: async_sessionmaker):
    await message.delete()
    async with db.begin() as session:
        user = await session.get(User, message.from_user.id)
        user.kai_user.group.pinned_text = message.text

    state_data = await state.get_data()
    call = CallbackQuery(**state_data['main_call'])

    await state.clear()
    await show_my_group(call)


@router.callback_query(Action.filter(F.name == Action.Name.clear_pinned_text))
async def clear_pin_text(call: CallbackQuery, state: FSMContext, db: async_sessionmaker):
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.kai_user.group.pinned_text = None

    await state.clear()
    await show_my_group(call)


@router.callback_query(Navigation.filter(F.to == Navigation.To.documents))
async def show_documents(call: CallbackQuery):
    await call.message.edit_text(_(messages.documents), reply_markup=inline_keyboards.get_documents_keyboard())
    await call.answer()


@router.callback_query(Action.filter(F.name == Action.Name.send_document))
async def send_document(call: CallbackQuery, callback_data: Action, db: async_sessionmaker, redis: Redis):
    async with db() as session:
        user = await session.get(User, call.from_user.id)

    match callback_data.payload:
        case 'syllabus':
            file_url = user.kai_user.group.syllabus
            caption = _(buttons.syllabus)
        case 'program':
            file_url = user.kai_user.group.educational_program
            caption = _(buttons.educational_program)
        case 'schedule':
            file_url = user.kai_user.group.study_schedule
            caption = _(buttons.study_schedule)
        case _:
            await call.answer(_(messages.base_error), show_alert=True)
            return

    if not file_url:
        await call.answer(_(messages.no_document), show_alert=True)
        return

    file_id = await redis.get(file_url)
    file = file_id.decode() if file_id else URLInputFile(file_url)

    msg = await call.message.answer_document(file, caption=caption)
    await call.answer()

    if not file_id:
        await redis.set(file_url, msg.document.file_id, ex=86400)
