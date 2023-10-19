import datetime
import logging

from aiogram import Dispatcher
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils import markdown as md
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks, states
from tgbot.misc.texts import messages, templates, rights, roles
from tgbot.services.database.models import User, GroupLesson, Homework, KAIUser
from tgbot.services.database.utils import get_lessons_with_homework
from tgbot.services.kai_parser.utils import lesson_type_to_text, lesson_type_to_emoji
from tgbot.services.utils.other import broadcast_text


def form_day_with_details(_, lessons: list[GroupLesson], date, use_emoji: bool):
    convert_lesson_type = lesson_type_to_emoji if use_emoji else lesson_type_to_text

    str_lessons = list()
    for lesson in lessons:
        if lesson.homework:
            homework = _(messages.homework).format(homework=lesson.homework[0].description)
        else:
            homework = _(messages.no_homework)

        str_lessons.append(messages.lesson_details.format(
            start_time=lesson.start_time.strftime('%H:%M'),
            lesson_type=convert_lesson_type(lesson.lesson_type),
            lesson_name=lesson.discipline.name,
            homework=homework
        ))

    if not str_lessons:
        str_lessons = [_(messages.day_off)]

    msg = templates.schedule_day_template.format(
        day_of_week=templates.week_day.format(
            pointer='',
            day=_(messages.week_days[date.weekday()]),
            date=date.strftime("%d.%m.%Y")
        ),
        lessons='\n\n'.join(str_lessons) + '\n'
    )

    return msg


async def check_access(_, call, tg_user):
    if not tg_user.has_role(roles.admin):
        if not tg_user.has_role(roles.verified):
            await call.answer(_(messages.details_not_verified), show_alert=True)
            raise CancelHandler()

        if tg_user.kai_user.group_id != tg_user.group_id:
            await call.answer(_(messages.details_not_your_group), show_alert=True)
            raise CancelHandler()


async def show_day_details(call: CallbackQuery, callback_data: dict, _, db: async_sessionmaker):
    date = datetime.date.fromisoformat(callback_data['payload'])
    async with db() as session:
        tg_user = await session.get(User, call.from_user.id)

        await check_access(_, call, tg_user)

        edit_homework_right = tg_user.has_right_to(rights.edit_homework)
        lessons = await get_lessons_with_homework(session, tg_user.group_id, date)

    await call.message.edit_text(
        form_day_with_details(_, lessons, date, tg_user.use_emoji),
        reply_markup=inline_keyboards.get_day_details_keyboard(_, lessons, date, edit_homework_right)
    )
    await call.answer()


async def show_week_details(call: CallbackQuery, callback_data: dict, _, db: async_sessionmaker):
    week_first_date = datetime.datetime.fromisoformat(callback_data['payload'])
    week_first_date -= datetime.timedelta(days=week_first_date.weekday() % 7)

    all_lessons = list()
    all_dates = list()
    async with db.begin() as session:
        tg_user = await session.get(User, call.from_user.id)

        await check_access(_, call, tg_user)

        edit_homework_right = tg_user.has_right_to(rights.edit_homework)

        all_lessons_text = ''
        for week_day in range(6):
            day = week_first_date + datetime.timedelta(days=week_day)
            lessons = await get_lessons_with_homework(session, tg_user.group_id, day)
            all_lessons.extend(lessons), all_dates.extend([day.date()] * len(lessons))
            msg = form_day_with_details(_, lessons, day, tg_user.use_emoji)
            all_lessons_text += msg

    await call.message.edit_text(
        all_lessons_text,
        reply_markup=inline_keyboards.get_week_details_keyboard(_, all_lessons, all_dates, edit_homework_right)
    )
    await call.answer()


async def show_lesson_menu(call: CallbackQuery, callback_data: dict, _, db: async_sessionmaker):
    date = datetime.date.fromisoformat(callback_data['date'])
    async with db() as session:
        homework = await Homework.get_by_lesson_and_date(session, int(callback_data['lesson_id']), date)
        if homework is None:
            lesson = await session.get(GroupLesson, int(callback_data['lesson_id']))
        else:
            lesson = homework.lesson

    text = _(messages.lesson_homework_edit).format(
        date=date.isoformat(),
        discipline=lesson.discipline.name,
        parity=lesson.parity_of_week,
        start_time=lesson.start_time.strftime('%H:%M'),
        homework=homework.description if homework else _(messages.no_homework)
    )
    keyboard = inline_keyboards.get_homework_keyboard(_, lesson.id, date, homework, callback_data['payload'])

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


async def start_homework_edit_or_add(call: CallbackQuery, callback_data: dict, state: FSMContext, _,
                                     db: async_sessionmaker):
    payload = f'{callback_data["lesson_id"]};{callback_data["date"]};{callback_data["payload"]}'
    keyboard = inline_keyboards.get_cancel_keyboard(_, to='homework', payload=payload)
    if callback_data['action'] == 'add':
        text = _(messages.homework_input)
    else:
        date, lesson_id = datetime.date.fromisoformat(callback_data['date']), int(callback_data['lesson_id'])
        async with db() as session:
            homework = await Homework.get_by_lesson_and_date(session, lesson_id, date)
        if homework:
            text = _(messages.edit_homework).format(homework=md.hcode(homework.description))
        else:
            callback_data['action'] = 'add'
            text = _(messages.homework_input)

    await call.message.edit_text(text, reply_markup=keyboard)
    await state.update_data(main_call=call.to_python(), **callback_data)
    await states.Homework.waiting_for_homework.set()
    await call.answer()


async def get_homework(message: Message, state: FSMContext, _, db: async_sessionmaker):
    homework_description = message.text
    state_data = await state.get_data()
    lesson_id = int(state_data['lesson_id'])
    date = datetime.date.fromisoformat(state_data['date'])
    main_call = CallbackQuery(**state_data['main_call'])

    async with db.begin() as session:
        homework = await Homework.get_by_lesson_and_date(session, lesson_id, date)
        if homework:
            logging.info(f'[{message.from_user.id}] Edited homework {date} {homework.lesson.start_time} - {homework_description}')
            homework.description = homework_description
        else:
            lesson = await session.get(GroupLesson, lesson_id)
            logging.info(f'[{message.from_user.id}] Added homework {date} {lesson.start_time} - {homework_description}')
            chats_ids = await KAIUser.get_telegram_ids_by_group(session, lesson.group_id)
            homework = Homework(
                description=homework_description,
                date=date,
                lesson_id=lesson_id
            )
            session.add(homework)

    await message.delete()
    await state.clear()
    await show_lesson_menu(main_call, {'lesson_id': lesson_id, 'date': date.isoformat(), 'payload': state_data['payload']})

    if state_data['action'] == 'add':
        await broadcast_text(
            _,
            chats=chats_ids,
            text=messages.new_homework,
            format_kwargs={
                'date': homework.date,
                'discipline': lesson.discipline.name,
                'homework': homework.description
            },
            bot=message.bot,
            db=db
        )


async def delete_homework(call: CallbackQuery, callback_data: dict, _, db: async_sessionmaker):
    date = datetime.date.fromisoformat(callback_data['date'])
    async with db.begin() as session:
        homework = await Homework.get_by_lesson_and_date(session, int(callback_data['lesson_id']), date)
        if homework:
            logging.info(f'[{call.from_user.id}] Deleted homework {date} {homework.lesson.start_time}')
            await session.delete(homework)

    await show_lesson_menu(call, callback_data)


def register_details(dp: Dispatcher):
    dp.register_callback_query_handler(show_day_details, callbacks.schedule.filter(action='day_details'), state='*')
    dp.register_callback_query_handler(show_week_details, callbacks.schedule.filter(action='week_details'), state='*')
    dp.register_callback_query_handler(show_lesson_menu, callbacks.details.filter(action='show'), state='*')
    dp.register_callback_query_handler(start_homework_edit_or_add, callbacks.details.filter(action='add'), state='*')
    dp.register_callback_query_handler(start_homework_edit_or_add, callbacks.details.filter(action='edit'), state='*')
    dp.register_callback_query_handler(delete_homework, callbacks.details.filter(action='delete'), state='*')

    dp.register_message_handler(get_homework, state=states.Homework.waiting_for_homework)
