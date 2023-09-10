from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md

import tgbot.keyboards.inline_keyboards as inline
import tgbot.misc.callbacks as callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import User, GroupLesson
from tgbot.services.database.utils import get_group_teachers
from tgbot.services.kai_parser.utils import lesson_type_to_emoji


def form_teachers_str(teachers: dict):
    teachers_str = ''
    for teacher in teachers:
        lesson_name = teachers[teacher]['lesson_name']
        if lesson_name == 'Физическая культура и спорт (элективная дисциплина)':
            lesson_types = lesson_type_to_emoji('физ')
        else:
            lesson_types = ' '.join(map(lesson_type_to_emoji, teachers[teacher]['lesson_types']))

        teachers_str += messages.teacher.format(
            lesson_name=md.hbold(lesson_name),
            lesson_types=lesson_types,
            departament=teachers[teacher]['departament'],
            full_name=md.hcode(teacher)
        )

    return teachers_str


async def show_teachers(call: CallbackQuery):
    db_session = call.bot.get('database')
    _ = call.bot.get('_')

    async with db_session() as session:
        user = await session.get(User, call.from_user.id)

        if not user.group_id:
            await call.answer(_(messages.select_group), show_alert=True)
            return

        teachers = await get_group_teachers(session, user.group_id)
        if not teachers:
            await call.answer(_(messages.kai_error), show_alert=True)
            return

    teachers_str = form_teachers_str(teachers)
    msg = _(messages.teachers_template).format(teachers=teachers_str, group_name=md.hcode(user.group.group_name))
    await call.message.edit_text(msg, reply_markup=inline.get_teachers_keyboard(_, user.group.group_name))


def register_teachers(dp: Dispatcher):
    dp.register_callback_query_handler(show_teachers, callbacks.schedule.filter(action='teachers'), state='*')
