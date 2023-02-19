import datetime
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
import tgbot.misc.callbacks as callbacks

import tgbot.keyboards.inline_keyboards as inline
from tgbot.misc.texts import reply_commands, messages
from tgbot.services.database.models import User
from tgbot.services.kai_parser.helper import get_schedule_by_week_day


def form_lessons(schedule_list):
    lessons = []
    for i in schedule_list:
        if i.auditory_number == 'КСК КАИ ОЛИМП':
            i.building_number = 'ОЛИМП'
            i.auditory_number = ''
        else:
            i.building_number += ' зд.'
        lessons.append(messages.lesson_template.format(
            start_time=i.start_time.strftime('%H:%M'),
            end_time=i.end_time.strftime('%H:%M'),
            lesson_type=i.lesson_type,
            lesson_name=i.lesson_name,
            building=i.building_number,
            auditory=i.auditory_number
        ))
    lessons = '\n\n'.join(lessons) + '\n'
    return lessons


async def form_day(_, db, user, today, with_date=False):
    week_num = int(today.strftime("%V"))
    schedule_list = await get_schedule_by_week_day(user.group_id, today.isoweekday(),
                                                   2 if not week_num % 2 else 1, db)
    if not schedule_list:
        lessons = _('Day off\n')
    else:
        lessons = form_lessons(schedule_list)
    msg = messages.schedule_day_template.format(
        day_of_week=(_('Monday'),
                     _('Tuesday'),
                     _('Wednesday'),
                     _('Thursday'),
                     _('Friday'),
                     _('Saturday'),
                     _('Sunday'),)[today.weekday()] + f'({today.date().strftime("%d.%m.%Y")})' if with_date else '',
        lessons=lessons
    )

    return msg


async def send_schedule_menu(call: CallbackQuery):
    _ = call.bot.get('_')
    await call.message.edit_text(messages.schedule_menu, reply_markup=inline.get_main_schedule_keyboard(_))
    await call.answer()


async def send_today_schedule(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    _ = call.bot.get('_')

    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer('Выберите группу в профиле', show_alert=True)
            return
        else:
            today = datetime.datetime.strptime(callback_data['payload'], '%Y-%m-%d')
            week_num = int(today.strftime("%V"))
            msg = await form_day(_, db, user, today)
            await call.message.edit_text(msg, reply_markup=inline.get_schedule_day_keyboard(_, week_num % 2, today))
    await call.answer()


async def send_full_schedule(call: CallbackQuery):
    db = call.bot.get('database')
    _ = call.bot.get('_')
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer('Выберите группу в профиле', show_alert=True)
            return
        else:
            today = datetime.datetime.now()
            today -= datetime.timedelta(days=today.weekday())
            week_num = int(today.strftime("%V"))
            all_lessons = ''
            for i in range(6):
                msg = await form_day(_, db, user, today + datetime.timedelta(days=i), True)
                all_lessons += msg
                print(msg)
            await call.message.edit_text(all_lessons)
    await call.answer()


def register_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(send_today_schedule, callbacks.schedule.filter(action='show_day'))
    dp.register_callback_query_handler(send_schedule_menu, callbacks.schedule.filter(action='main_menu'))
    dp.register_callback_query_handler(send_full_schedule, callbacks.schedule.filter(action='full_schedule'))
