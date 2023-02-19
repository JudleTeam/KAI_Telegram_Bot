import datetime
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
import tgbot.misc.callbacks as callbacks

import tgbot.keyboards.inline_keyboards as inline
from tgbot.misc.texts import reply_commands, messages
from tgbot.services.database.models import User
from tgbot.services.kai_parser.helper import get_schedule_by_week_day


async def send_today_schedule(call: CallbackQuery):
    db = call.bot.get('database')
    _ = call.bot.get('_')

    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        if not user.group_id:
            await call.answer('Выберите группу в профиле', show_alert=True)
            return
        else:
            week_num = int(datetime.datetime.now().strftime("%V"))
            schedule_list = await get_schedule_by_week_day(user.group_id, datetime.datetime.now().isoweekday(), week_num % 2, db)
            if not schedule_list:
                lessons = _('Day off')
            else:
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
            msg = messages.schedule_day_template.format(
                day_of_week=(_('Monday'),
                             _('Tuesday'),
                             _('Wednesday'),
                             _('Thursday'),
                             _('Friday'),
                             _('Saturday'),
                             _('Sunday'),)[datetime.datetime.now().weekday()],
                lessons=lessons
            )
            await call.message.edit_text(msg)


async def send_tomorrow_schedule(call: CallbackQuery):
    pass


async def send_day_after_tomorrow_schedule(call: CallbackQuery):
    pass


def register_schedule(dp: Dispatcher):
    dp.register_callback_query_handler(send_today_schedule, callbacks.schedule.filter(action='today'))
