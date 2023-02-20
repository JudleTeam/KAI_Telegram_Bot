from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md
from sqlalchemy import select

import tgbot.keyboards.inline_keyboards as inline
import tgbot.misc.callbacks as callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import User, GroupTeacher
from tgbot.services.kai_parser.helper import lesson_type_to_emoji, get_group_teachers


def form_teacher(teacher):
    if teacher.lesson_name == 'Физическая культура и спорт (элективная дисциплина)':
        teacher.lesson_type = 'физ'
    return messages.teacher.format(
        lesson_name=md.hbold(teacher.lesson_name),
        lesson_types=' '.join(lesson_type_to_emoji(teacher.lesson_type)),
        full_name=md.hcode(teacher.teacher_name)
    )


async def show_teachers(call: CallbackQuery):
    db = call.bot.get('database')
    _ = call.bot.get('_')

    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer('Выберите группу в профиле', show_alert=True)
            return

        stm = select(GroupTeacher).where(GroupTeacher.group_id == user.group_id)
        teachers = (await session.execute(stm)).scalars().all()
        if not teachers:
            teachers = await get_group_teachers(user.group_id, db)
            if not teachers:
                await call.answer('Произошла ошибка', show_alert=True)
                return
        a = ''
        for teacher in teachers:
            a += form_teacher(teacher)
        msg = messages.teachers_template.format(
            teachers=a
        )
        await call.message.edit_text(msg, reply_markup=inline.get_teachers_keyboard(_))


def register_teachers(dp: Dispatcher):
    dp.register_callback_query_handler(show_teachers, callbacks.schedule.filter(action='teachers'))
