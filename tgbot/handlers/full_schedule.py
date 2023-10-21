from aiogram import Router
from aiogram.exceptions import AiogramError
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.keyboards import inline_keyboards
from tgbot.misc.callbacks import FullSchedule
from tgbot.misc.texts import messages, templates
from tgbot.services.database.models import User, GroupLesson
from tgbot.services.kai_parser.utils import lesson_type_to_emoji, lesson_type_to_text


router = Router()


def form_full_schedule_day(_, lessons: list[GroupLesson], week_day: int, show_teachers: bool, use_emoji: bool):
    lessons_str_list = list()

    convert_lesson_type = lesson_type_to_emoji if use_emoji else lesson_type_to_text

    for lesson in lessons:
        if lesson.auditory_number == 'КСК КАИ ОЛИМП':
            lesson.building_number = 'ОЛИМП'
            lesson.auditory_number = ''
            lesson.lesson_type = 'физ'
        else:
            lesson.building_number += ' зд.'

        if lesson.auditory_number.isdigit():
            lesson.auditory_number += ' ауд.'

        teacher = ''
        if show_teachers:
            if lesson.teacher:
                teacher = templates.teacher_in_schedule.format(name=lesson.teacher.short_name,
                                                               departament=lesson.teacher.departament.short_name)
            else:
                teacher = '\nПреподаватель кафедры'

        lessons_str_list.append(templates.lesson_template.format(
            start_time=lesson.start_time.strftime('%H:%M'),
            end_time=lesson.end_time.strftime('%H:%M') if lesson.end_time else '??:??',
            lesson_type=convert_lesson_type(lesson.lesson_type),
            lesson_name=md.hbold(lesson.discipline.name),
            building=lesson.building_number,
            auditory=lesson.auditory_number,
            parity=md.hitalic(lesson.parity_of_week or '-'),
            teacher=teacher,
            homework=''
        ))

    if not lessons_str_list:
        lessons_str_list =[ _(messages.day_off)]

    msg = templates.schedule_day_template.format(
        day_of_week=_(messages.week_days[week_day - 1]),
        lessons='\n\n'.join(lessons_str_list) + '\n'
    )

    return msg


@router.callback_query(FullSchedule.filter())
async def show_full_schedule(call: CallbackQuery, callback_data: FullSchedule, _, db: async_sessionmaker):
    async with db() as session:
        tg_user = await session.get(User, call.from_user.id)
        if not tg_user.group_id:
            await call.answer(_(messages.no_selected_group), show_alert=True)
            return

        all_lessons_text = ''
        for week_day in range(1, 7):
            if callback_data.parity == 0:
                lessons = await GroupLesson.get_group_day_schedule_with_any_parity(session, tg_user.group_id, week_day)
            else:
                lessons = await GroupLesson.get_group_day_schedule(session, tg_user.group_id, week_day, callback_data.parity)
            msg = form_full_schedule_day(_, lessons, week_day, tg_user.show_teachers_in_schedule, tg_user.use_emoji)
            all_lessons_text += msg

    try:
        await call.message.edit_text(
            all_lessons_text,
            reply_markup=inline_keyboards.get_full_schedule_keyboard(_, callback_data.parity, tg_user.group.group_name)
        )
    except AiogramError:
        pass

    await call.answer()
