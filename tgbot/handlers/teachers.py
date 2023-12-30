import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils import markdown as md
from aiogram.utils.i18n import gettext as _
from sqlalchemy.ext.asyncio import async_sessionmaker

import tgbot.keyboards.inline_keyboards as inline
from tgbot.misc.callbacks import Navigation
from tgbot.misc.texts import messages, templates, buttons
from tgbot.services.database.models import User, Teacher, GroupLesson
from tgbot.services.database.utils import get_group_teachers_dict, get_group_teachers
from tgbot.services.kai_parser.utils import lesson_type_to_emoji, lesson_type_to_text

router = Router()

MAX_TEACHER_SCHEDULE_LENGTH = 4000
TEACHERS_SEARCH_RESULTS_LIMIT = 20
CACHE_TIME = 900


def form_teachers_str(teachers: dict):
    teachers_str = ''
    for teacher in teachers:
        lesson_name = teachers[teacher]['lesson_name']
        if lesson_name == 'Физическая культура и спорт (элективная дисциплина)':
            lesson_types = lesson_type_to_emoji('физ')
        else:
            lesson_types = ' '.join(map(lesson_type_to_emoji, teachers[teacher]['lesson_types']))

        teachers_str += templates.teacher.format(
            lesson_name=md.hbold(lesson_name),
            lesson_types=lesson_types,
            departament=teachers[teacher]['departament'],
            full_name=md.hcode(teacher)
        )

    return teachers_str


def form_teachers_lessons(teacher_lessons: list[GroupLesson], use_emoji: bool, week_parity: int, cut_after: None | int = None):
    convert_lesson_type = lesson_type_to_emoji if use_emoji else lesson_type_to_text
    result_str = ''
    for day in range(1, 6 + 1):
        day_lessons = list(filter(lambda x: x.number_of_day == day, teacher_lessons))
        day_lessons_parts = list()
        printed_lessons = set()
        for lesson in day_lessons:
            lesson_signature = (lesson.number_of_day, lesson.parity_of_week, lesson.start_time)
            if lesson_signature in printed_lessons:
                continue

            building_number = lesson.building_number
            auditory_number = lesson.auditory_number
            lesson_type = lesson.lesson_type
            if lesson.auditory_number == 'КСК КАИ ОЛИМП':
                building_number = 'ОЛИМП'
                auditory_number = ''
                lesson_type = 'физ'
            else:
                building_number += ' зд.'

            if lesson.auditory_number.isdigit():
                auditory_number += ' ауд.'

            group_names = [str(x.group.group_name) for x in day_lessons if
                           x.parity_of_week == lesson.parity_of_week and x.start_time == lesson.start_time]
            printed_lessons.add(lesson_signature)
            lesson_str = templates.teacher_lesson.format(
                start_time=lesson.start_time.strftime('%H:%M'),
                end_time=lesson.end_time.strftime('%H:%M') if lesson.end_time else '??:??',
                building=building_number,
                auditory=auditory_number,
                parity=md.hitalic(lesson.parity_of_week or '-'),
                lesson_type=convert_lesson_type(lesson_type),
                lesson_name=md.hbold(lesson.discipline.name),
                group_names=', '.join(group_names)
            )

            if lesson.int_parity_of_week == week_parity or lesson.int_parity_of_week == 0:
                lesson_str = '→ ' + lesson_str

            day_lessons_parts.append(lesson_str)

        day_lessons_str = '\n\n'.join(day_lessons_parts) if day_lessons_parts else _(messages.day_off)
        day_str = templates.schedule_day_template.format(
            day_of_week=_(messages.week_days[day - 1]),
            lessons=day_lessons_str + '\n'
        )

        if cut_after is not None and len(result_str + day_str) > cut_after:
            result_str += _(messages.schedule_too_long) + '\n'
            break
        else:
            result_str += day_str

    return result_str


@router.callback_query(Navigation.filter(F.to == Navigation.To.teachers))
async def show_teachers(call: CallbackQuery, state: FSMContext, db: async_sessionmaker):
    await state.clear()
    async with db() as session:
        user = await session.get(User, call.from_user.id)

        if not user.group_id:
            await call.answer(_(messages.no_selected_group), show_alert=True)
            return

        teachers = await get_group_teachers_dict(session, user.group_id)
        if not teachers:
            await call.answer(_(messages.kai_error), show_alert=True)
            return

    teachers_str = form_teachers_str(teachers)
    msg = _(messages.teachers_template).format(teachers=teachers_str, group_name=md.hcode(user.group.group_name))
    await call.message.edit_text(msg, reply_markup=inline.get_teachers_keyboard(user.group.group_name))


async def create_teachers_inline_result(session, teachers: list[Teacher], use_emoji):
    int_week_parity = int(datetime.datetime.now().strftime("%V")) % 2
    week_parity = _(buttons.odd_week) if int_week_parity else _(buttons.even_week)
    int_week_parity = 1 if int_week_parity else 2

    result = list()
    for teacher in teachers:
        teacher_lessons: list[GroupLesson] = await GroupLesson.get_teacher_schedule(session, teacher.login)

        schedule_text = _(messages.teacher_schedule).format(
            name=teacher.name,
            departament=teacher.departament.name,
            schedule=form_teachers_lessons(teacher_lessons, use_emoji, int_week_parity, cut_after=MAX_TEACHER_SCHEDULE_LENGTH),
            parity=week_parity
        )

        result.append(
            InlineQueryResultArticle(
                id=teacher.login,
                title=teacher.name,
                input_message_content=InputTextMessageContent(message_text=schedule_text),
                description=teacher.departament.name
            )
        )

    return result


@router.inline_query(F.query == '')
async def search_group_teachers(inline_query: InlineQuery, db: async_sessionmaker):
    """
    При пустом поисковом запросе выводятся преподаватели выбранной (не родной) группы
    """

    if inline_query.offset:
        offset = int(inline_query.offset)
    else:
        offset = 0

    async with db() as session:
        tg_user = await session.get(User, inline_query.from_user.id)
        if tg_user is None:
            # Если пользователь не зарегистрирован, то для него нельзя вывести преподавателей
            return

        group_teachers = await get_group_teachers(session, tg_user.group_id, limit=TEACHERS_SEARCH_RESULTS_LIMIT, offset=offset)

        result = await create_teachers_inline_result(session, group_teachers, tg_user.use_emoji)

    if len(group_teachers) < TEACHERS_SEARCH_RESULTS_LIMIT:
        next_offset = ''
    else:
        next_offset = str(offset + TEACHERS_SEARCH_RESULTS_LIMIT)

    await inline_query.answer(result, next_offset=next_offset, cache_time=CACHE_TIME, is_personal=True)


@router.inline_query(F.query != '')
async def search_teachers(inline_query: InlineQuery, db: async_sessionmaker):
    if inline_query.offset:
        offset = int(inline_query.offset)
    else:
        offset = 0

    async with db() as session:
        tg_user = await session.get(User, inline_query.from_user.id)
        if tg_user is not None:
            use_emoji = tg_user.use_emoji
        else:
            use_emoji = True

        match len(inline_query.query.split()):
            case 1:
                similarity = 0.2
            case 2:
                similarity = 0.4
            case _:
                similarity = 0.6

        teachers = await Teacher.search_by_name(session, inline_query.query.replace('ё', 'е'),
                                                similarity=similarity, limit=TEACHERS_SEARCH_RESULTS_LIMIT, offset=offset)
        if tg_user is not None and tg_user.group_id is not None:
            group_teachers = await get_group_teachers(session, tg_user.group_id)

            sorted_teachers = list()
            for teacher in teachers:
                if teacher in group_teachers:
                    sorted_teachers.insert(0, teacher)
                else:
                    sorted_teachers.append(teacher)
        else:
            sorted_teachers = teachers

        result = await create_teachers_inline_result(session, sorted_teachers, use_emoji)

    if len(sorted_teachers) < TEACHERS_SEARCH_RESULTS_LIMIT:
        next_offset = None
    else:
        next_offset = str(offset + TEACHERS_SEARCH_RESULTS_LIMIT)

    await inline_query.answer(result, next_offset=next_offset, cache_time=CACHE_TIME, is_personal=True)
