import datetime
import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md, markdown
from aiogram.utils.exceptions import MessageNotModified

import tgbot.keyboards.inline_keyboards as inline
import tgbot.misc.callbacks as callbacks
from tgbot.misc.texts import messages, buttons
from tgbot.services.database.models import User
from tgbot.services.kai_parser.utils import (get_schedule_by_week_day, lesson_type_to_emoji, add_group_schedule,
                                             lesson_type_to_text)


def convert_day(today: str):
    return datetime.datetime.strptime(today, '%Y-%m-%d %H:%M:%S')


def form_lessons(schedule_list):
    lessons = []
    for lesson in schedule_list:
        if lesson.auditory_number == 'КСК КАИ ОЛИМП':
            lesson.building_number = 'ОЛИМП'
            lesson.auditory_number = ''
            lesson.lesson_type = 'физ'
        else:
            lesson.building_number += ' зд.'

        if lesson.auditory_number.isdigit():
            lesson.auditory_number += ' ауд.'

        lessons.append(messages.lesson_template.format(
            start_time=lesson.start_time.strftime('%H:%M'),
            end_time=lesson.end_time.strftime('%H:%M'),
            lesson_type=lesson_type_to_emoji(lesson.lesson_type)[0],
            lesson_name=markdown.hbold(lesson.lesson_name),
            building=lesson.building_number,
            auditory=lesson.auditory_number,
            parity=md.hitalic(lesson.parity_of_week or '-')
        ))
    lessons = '\n\n'.join(lessons) + '\n'
    return lessons


async def form_day(_, db, user, today, with_date=False, with_pointer=False):
    week_num = int(today.strftime("%V"))
    if with_pointer and today.date() == datetime.datetime.now().date():
        with_pointer = True
    else:
        with_pointer = False
    schedule_list = await get_schedule_by_week_day(user.group_id, today.isoweekday(), 2 if not week_num % 2 else 1, db)
    if not schedule_list or not schedule_list[0].lesson_name:
        lessons = _('Day off\n')
    else:
        lessons = form_lessons(schedule_list)
    msg = messages.schedule_day_template.format(
        day_of_week=(messages.full_schedule_pointer if with_pointer else '') +
                    (
                        _('Monday'),
                        _('Tuesday'),
                        _('Wednesday'),
                        _('Thursday'),
                        _('Friday'),
                        _('Saturday'),
                        _('Sunday'),
                    )[today.weekday()] + (f' ({today.date().strftime("%d.%m.%Y")})' if with_date else ''),
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
    await call.message.edit_text(msg, reply_markup=inline.get_main_schedule_keyboard(_, group_name))
    await call.answer()


async def send_today_schedule(call: CallbackQuery, callback_data: dict):
    db, _ = call.bot.get('database'), call.bot.get('_')
    async with db() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer(_(messages.select_group), show_alert=True)
            return

    if callback_data['payload'] == 'today':
        today = datetime.datetime.now()
    else:
        today = datetime.datetime.strptime(callback_data['payload'], '%Y-%m-%d')

    msg = await form_day(_, db, user, today, with_date=True)
    keyboard = inline.get_schedule_day_keyboard(_, today, user.group.group_name)
    try:
        await call.message.edit_text(msg, reply_markup=keyboard)
    except MessageNotModified as e:
        pass

    await call.answer()


async def send_full_schedule(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    _ = call.bot.get('_')
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer(_(messages.select_group), show_alert=True)
            return

    today = datetime.datetime.now()
    if callback_data['payload'] == 'change':
        today += datetime.timedelta(days=7)
    today -= datetime.timedelta(days=today.weekday())
    all_lessons = ''
    for i in range(6):
        try:
            if callback_data['payload'] == 'change':
                msg = await form_day(_, db, user, today + datetime.timedelta(days=i), False, True)
            else:
                msg = await form_day(_, db, user, today + datetime.timedelta(days=i), True, True)
            all_lessons += msg
        except Exception as e:
            logging.error(f'[{call.from_user.id}]: Error with group {user.group.group_name} full schedule - {e}')
            await call.answer(_(messages.kai_error), show_alert=True)
            return
    await call.message.edit_text(all_lessons,
                                 reply_markup=inline.get_full_schedule_keyboard(_, user.group.group_name))

    await call.answer()


async def switch_show_parity(call: CallbackQuery, state: FSMContext):
    db = call.bot.get('database')
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.is_shown_parity = not user.is_shown_parity
    await show_schedule_menu(call, state)
    await call.answer()


def register_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(send_today_schedule, callbacks.schedule.filter(action='show_day'), state='*')
    dp.register_callback_query_handler(show_schedule_menu, callbacks.schedule.filter(action='main_menu'), state='*')
    dp.register_callback_query_handler(send_full_schedule, callbacks.schedule.filter(action='full_schedule'), state='*')
    dp.register_callback_query_handler(switch_show_parity, callbacks.schedule.filter(action='switch_show_parity'), state='*')
