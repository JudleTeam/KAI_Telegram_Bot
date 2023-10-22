import datetime
import logging

from aiogram import Router, F, Dispatcher, Bot
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils import markdown as md
from aiogram.utils.i18n import gettext as _
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.keyboards import inline_keyboards
from tgbot.middlewares.language import CacheAndDatabaseI18nMiddleware
from tgbot.misc import states
from tgbot.misc.callbacks import Schedule, Details, Cancel
from tgbot.misc.texts import messages, templates, rights, roles
from tgbot.services.database.models import User, GroupLesson, Homework, KAIUser
from tgbot.services.database.utils import get_lessons_with_homework
from tgbot.services.kai_parser.utils import lesson_type_to_text, lesson_type_to_emoji
from tgbot.services.utils.other import broadcast_text


router = Router()


def form_day_with_details(lessons: list[GroupLesson], date, use_emoji: bool):
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


async def check_access(call, tg_user):
    if not tg_user.has_role(roles.admin):
        if not tg_user.has_role(roles.verified):
            await call.answer(_(messages.details_not_verified), show_alert=True)
            raise CancelHandler()

        if tg_user.kai_user.group_id != tg_user.group_id:
            await call.answer(_(messages.details_not_your_group), show_alert=True)
            raise CancelHandler()


@router.callback_query(Schedule.filter(F.action == Schedule.Action.day_details))
async def show_day_details(call: CallbackQuery, callback_data: Schedule, db: async_sessionmaker):
    date = datetime.date.fromisoformat(callback_data.date)
    async with db() as session:
        tg_user = await session.get(User, call.from_user.id)

        await check_access(call, tg_user)

        edit_homework_right = tg_user.has_right_to(rights.edit_homework)
        lessons = await get_lessons_with_homework(session, tg_user.group_id, date)

    await call.message.edit_text(
        form_day_with_details(lessons, date, tg_user.use_emoji),
        reply_markup=inline_keyboards.get_day_details_keyboard(lessons, date, edit_homework_right)
    )
    await call.answer()


@router.callback_query(Schedule.filter(F.action == Schedule.Action.week_details))
async def show_week_details(call: CallbackQuery, callback_data: Schedule, db: async_sessionmaker):
    week_first_date = datetime.datetime.fromisoformat(callback_data.date)
    week_first_date -= datetime.timedelta(days=week_first_date.weekday() % 7)

    all_lessons = list()
    all_dates = list()
    async with db.begin() as session:
        tg_user = await session.get(User, call.from_user.id)

        await check_access(call, tg_user)

        edit_homework_right = tg_user.has_right_to(rights.edit_homework)

        all_lessons_text = ''
        for week_day in range(6):
            day = week_first_date + datetime.timedelta(days=week_day)
            lessons = await get_lessons_with_homework(session, tg_user.group_id, day)
            all_lessons.extend(lessons), all_dates.extend([day.date()] * len(lessons))
            msg = form_day_with_details(lessons, day, tg_user.use_emoji)
            all_lessons_text += msg

    await call.message.edit_text(
        all_lessons_text,
        reply_markup=inline_keyboards.get_week_details_keyboard(all_lessons, all_dates, edit_homework_right)
    )
    await call.answer()


@router.callback_query(Details.filter(F.action == Details.Action.show))
async def show_lesson_menu(call: CallbackQuery, callback_data: Details, db: async_sessionmaker):
    date = datetime.date.fromisoformat(callback_data.date)
    async with db() as session:
        homework = await Homework.get_by_lesson_and_date(session, callback_data.lesson_id, date)
        if homework is None:
            lesson = await session.get(GroupLesson, callback_data.lesson_id)
        else:
            lesson = homework.lesson

    text = _(messages.lesson_homework_edit).format(
        date=date.isoformat(),
        discipline=lesson.discipline.name,
        parity=lesson.parity_of_week,
        start_time=lesson.start_time.strftime('%H:%M'),
        homework=homework.description if homework else _(messages.no_homework)
    )
    keyboard = inline_keyboards.get_homework_keyboard(lesson.id, date, homework, callback_data.payload)

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@router.callback_query(Details.filter(F.action == Details.Action.add))
@router.callback_query(Details.filter(F.action == Details.Action.edit))
async def start_homework_edit_or_add(call: CallbackQuery, callback_data: Details, state: FSMContext,
                                     db: async_sessionmaker):
    payload = f'{callback_data.lesson_id};{callback_data.date};{callback_data.payload}'
    keyboard = inline_keyboards.get_cancel_keyboard(to=Cancel.To.homework, payload=payload)
    if callback_data.action == Details.Action.add:
        text = _(messages.homework_input)
    else:
        async with db() as session:
            homework = await Homework.get_by_lesson_and_date(session, callback_data.lesson_id, callback_data.date)
        if homework:
            text = _(messages.edit_homework).format(homework=md.hcode(homework.description))
        else:
            callback_data['action'] = 'add'
            text = _(messages.homework_input)

    await call.message.edit_text(text, reply_markup=keyboard)
    await state.update_data(main_call=call.to_python(), **callback_data.model_dump())
    await state.set_state(states.Homework.waiting_for_homework)
    await call.answer()


@router.message(states.Homework.waiting_for_homework)
async def get_homework(message: Message, state: FSMContext, db: async_sessionmaker, bot: Bot, redis: Redis,
                       i18n_middleware: CacheAndDatabaseI18nMiddleware):
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
            chats=chats_ids,
            text=messages.new_homework,
            format_kwargs={
                'date': homework.date,
                'discipline': lesson.discipline.name,
                'homework': homework.description
            },
            bot=bot,
            db=db,
            redis=redis,
            i18n=i18n_middleware
        )


@router.callback_query(Details.filter(F.action == Details.Action.delete))
async def delete_homework(call: CallbackQuery, callback_data: Details, db: async_sessionmaker):
    async with db.begin() as session:
        homework = await Homework.get_by_lesson_and_date(session, callback_data.lesson_id, callback_data.date)
        if homework:
            logging.info(f'[{call.from_user.id}] Deleted homework {callback_data.date} {homework.lesson.start_time}')
            await session.delete(homework)

    await show_lesson_menu(call, callback_data)
