import datetime
import logging
from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md, markdown
from aiogram.utils.exceptions import MessageNotModified

import tgbot.keyboards.inline_keyboards as inline
import tgbot.misc.callbacks as callbacks
from tgbot.misc.texts import messages, buttons, templates
from tgbot.services.database.models import User, GroupLesson
from tgbot.services.kai_parser.utils import lesson_type_to_emoji, lesson_type_to_text


def convert_day(today: str):
    return datetime.datetime.strptime(today, '%Y-%m-%d %H:%M:%S')


def form_lessons(schedule_list: list[GroupLesson], show_teachers: bool, use_emoji: bool):
    lessons = list()

    convert_lesson_type = lesson_type_to_emoji if use_emoji else lesson_type_to_text

    for lesson in schedule_list:
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

        lessons.append(templates.lesson_template.format(
            start_time=lesson.start_time.strftime('%H:%M'),
            end_time=lesson.end_time.strftime('%H:%M'),
            lesson_type=convert_lesson_type(lesson.lesson_type),
            lesson_name=markdown.hbold(lesson.discipline.name),
            building=lesson.building_number,
            auditory=lesson.auditory_number,
            parity=md.hitalic(lesson.parity_of_week or '-'),
            teacher=teacher,
            homework=''
        ))

    lessons = '\n\n'.join(lessons) + '\n'
    return lessons


async def form_day(_, db, user, today, with_pointer=False):
    week_num = int(today.strftime('%V'))
    if with_pointer and today.date() == datetime.datetime.now().date():
        with_pointer = True
    else:
        with_pointer = False

    int_parity = 2 if not week_num % 2 else 1
    async with db() as session:
        schedule = await GroupLesson.get_group_day_schedule(session, user.group_id, today.isoweekday(), int_parity)

    if not schedule:
        lessons = _('Day off\n')
    else:
        lessons = form_lessons(schedule, user.show_teachers_in_schedule, user.use_emoji)

    msg = templates.schedule_day_template.format(
        day_of_week=templates.week_day.format(
            pointer=messages.full_schedule_pointer if with_pointer else '',
            day=_(messages.week_days[today.weekday()]),
            date=today.date().strftime("%d.%m.%Y")
        ),
        lessons=lessons
    )

    return msg


async def show_schedule_menu(call: CallbackQuery, state: FSMContext):
    await state.finish()
    _ = call.bot.get('_')
    db_session = call.bot.get('database')
    async with db_session() as session:
        user = await session.get(User, call.from_user.id)
    group_name = user.group.group_name if user.group else '????'
    week_parity = int(datetime.datetime.now().strftime("%V")) % 2
    week_parity = _(buttons.odd_week) if week_parity else _(buttons.even_week)
    msg = _(messages.schedule_menu).format(
        week=md.hunderline(week_parity)
    )
    if user.use_emoji:
        msg += _(messages.emoji_hint)
    await call.message.edit_text(msg, reply_markup=inline.get_main_schedule_keyboard(_, group_name))
    await call.answer()


async def show_day_schedule(call: CallbackQuery, callback_data: dict):
    db, _ = call.bot.get('database'), call.bot.get('_')
    async with db() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer(_(messages.no_selected_group), show_alert=True)
            return

    if callback_data['payload'] == 'today':
        today = datetime.datetime.now()
    else:
        today = datetime.datetime.strptime(callback_data['payload'], '%Y-%m-%d')

    int_parity = 2 if not int(today.strftime('%V')) % 2 else 1
    parity = f'{_(messages.even_week) if int_parity == 2 else _(messages.odd_week)}'

    text = await form_day(_, db, user, today) + md.hitalic(parity)
    keyboard = inline.get_schedule_day_keyboard(_, today, user.group.group_name)
    try:
        await call.message.edit_text(text, reply_markup=keyboard)
    except MessageNotModified as e:
        pass

    await call.answer()


async def send_week_schedule(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    _ = call.bot.get('_')
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer(_(messages.no_selected_group), show_alert=True)
            return

    week_first_date = datetime.datetime.fromtimestamp(float(callback_data['payload']))
    week_first_date -= datetime.timedelta(days=week_first_date.weekday() % 7)

    all_lessons = ''
    for week_day in range(6):
        msg = await form_day(_, db, user, week_first_date + datetime.timedelta(days=week_day), True)
        all_lessons += msg

    await call.message.edit_text(all_lessons, reply_markup=inline.get_week_schedule_keyboard(_, week_first_date,
                                                                                             user.group.group_name))

    await call.answer()


def register_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(show_day_schedule, callbacks.schedule.filter(action='show_day'), state='*')
    dp.register_callback_query_handler(show_schedule_menu, callbacks.schedule.filter(action='main_menu'), state='*')
    dp.register_callback_query_handler(send_week_schedule, callbacks.schedule.filter(action='week_schedule'), state='*')
