import datetime
import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md
from aiogram.utils.exceptions import MessageNotModified

import tgbot.keyboards.inline_keyboards as inline
import tgbot.misc.callbacks as callbacks
from tgbot.misc import states
from tgbot.misc.texts import messages, buttons
from tgbot.services.database.models import User
from tgbot.services.kai_parser.utils import get_schedule_by_week_day, lesson_type_to_emoji, add_group_schedule


def convert_day(today: str):
    return datetime.datetime.strptime(today, '%Y-%m-%d %H:%M:%S')


def form_lessons(schedule_list, with_full_parity):
    lessons = []
    for i in schedule_list:
        if i.auditory_number == 'КСК КАИ ОЛИМП':
            i.building_number = 'ОЛИМП'
            i.auditory_number = ''
            i.lesson_type = 'физ'
        else:
            i.building_number += ' зд.'
        full_parity_msg = i.parity_of_week if with_full_parity else ''
        lessons.append(messages.lesson_template.format(
            start_time=i.start_time.strftime('%H:%M'),
            end_time=i.end_time.strftime('%H:%M'),
            lesson_type=lesson_type_to_emoji(i.lesson_type)[0],
            lesson_name=i.lesson_name,
            building=i.building_number,
            auditory=i.auditory_number
        ) + full_parity_msg)
    lessons = '\n\n'.join(lessons) + '\n'
    return lessons


async def form_day(_, db, user, today, with_date=False, with_pointer=False, with_full_parity=True):
    week_num = int(today.strftime("%V"))
    if with_pointer and today.date() == datetime.datetime.now().date():
        with_pointer = True
    else:
        with_pointer = False
    subgroup = 1
    schedule_list = await get_schedule_by_week_day(user.group_id, subgroup, today.isoweekday(), 2 if not week_num % 2 else 1, db)
    if not schedule_list or not schedule_list[0].lesson_name:
        lessons = _('Day off\n')
    else:
        lessons = form_lessons(schedule_list, with_full_parity)
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
    await call.message.edit_text(_(messages.schedule_menu).format(week=md.hunderline(week_parity)),
                                 reply_markup=inline.get_main_schedule_keyboard(_, group_name))
    await call.answer()


async def send_today_schedule(call: CallbackQuery, callback_data: dict, state: FSMContext):
    db, _ = call.bot.get('database'), call.bot.get('_')
    async with db() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer(_(messages.select_group), show_alert=True)
            return

    today = datetime.datetime.strptime(callback_data['payload'], '%Y-%m-%d')
    week_num = int(today.strftime("%V"))

    msg = await form_day(_, db, user, today, with_date=True)
    try:
        await call.message.edit_text(msg, reply_markup=inline.get_schedule_day_keyboard(_, week_num % 2, today,
                                                                                        user.group.group_name))
    except MessageNotModified as e:
        pass

    await call.answer()


async def change_week_parity(call: CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data['action'] == 'day':
        schedule_day = datetime.datetime.strptime(callback_data['payload'], '%Y-%m-%d')
        schedule_day_week_num = int(schedule_day.strftime("%V"))
        if schedule_day_week_num % 2 == 0:
            new_schedule_day = schedule_day + datetime.timedelta(days=7)
        else:
            new_schedule_day = schedule_day - datetime.timedelta(days=7)
        await send_today_schedule(call, dict(action='change_week', payload=str(new_schedule_day.date())), state)
    elif callback_data['action'] == 'week':
        week_parity = int(datetime.datetime.now().strftime("%V")) % 2
        if week_parity != int(callback_data['payload']):
            await send_full_schedule(call, dict(action='', payload=''))
        else:
            await send_full_schedule(call, dict(action='', payload='change'))
    await call.answer()


async def send_full_schedule(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    _ = call.bot.get('_')
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer(_(messages.select_group), show_alert=True)
            return

    # add 6110 schedule
    # await add_group_schedule(23325, db)
    # add 4120 schedule
    # await add_group_schedule(23551, db)
    today = datetime.datetime.now()
    if callback_data['payload'] == 'change':
        today += datetime.timedelta(days=7)
    today -= datetime.timedelta(days=today.weekday())
    week_num = int(today.strftime("%V"))
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
                                 reply_markup=inline.get_full_schedule_keyboard(_, week_num % 2, user.group.group_name))

    await call.answer()


def register_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(send_today_schedule, callbacks.schedule.filter(action='show_day'), state='*')
    dp.register_callback_query_handler(show_schedule_menu, callbacks.schedule.filter(action='main_menu'), state='*')
    dp.register_callback_query_handler(send_full_schedule, callbacks.schedule.filter(action='full_schedule'), state='*')
    dp.register_callback_query_handler(change_week_parity, callbacks.change_schedule_week.filter(), state='*')
