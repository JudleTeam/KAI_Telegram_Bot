import datetime
from pprint import pprint

from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import User, GroupLesson
from tgbot.services.database.utils import get_lessons_with_homework
from tgbot.services.kai_parser.utils import lesson_type_to_text, lesson_type_to_emoji


def form_day_with_details(_, lessons: list[GroupLesson], use_emoji: bool):
    convert_lesson_type = lesson_type_to_emoji if use_emoji else lesson_type_to_text

    str_lessons = list()
    for lesson in lessons:
        if lesson.homework:
            homework = lesson.homework[0].description
        else:
            homework = _(messages.no_homework)

        str_lessons.append(messages.lesson_details.format(
            lesson_type=convert_lesson_type(lesson.lesson_type),
            lesson_name=lesson.discipline.name,
            homework=homework
        ))

    return '\n\n'.join(str_lessons) + '\n'


async def show_day_details(call: CallbackQuery, callback_data: dict):
    db, _ = call.bot.get('database'), call.bot.get('_')
    date = datetime.date.fromisoformat(callback_data['payload'])
    async with db() as session:
        tg_user = await session.get(User, call.from_user.id)
        lessons = await get_lessons_with_homework(session, tg_user.group_id, date)

    await call.message.edit_text(
        form_day_with_details(_, lessons, tg_user.use_emoji),
        reply_markup=inline_keyboards.get_details_keyboard(_, lessons, date)
    )
    await call.answer()


def register_details(dp: Dispatcher):
    dp.register_callback_query_handler(show_day_details, callbacks.schedule.filter(action='details'))