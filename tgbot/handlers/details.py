import datetime
from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks, states
from tgbot.misc.texts import messages, templates
from tgbot.services.database.models import User, GroupLesson, Homework
from tgbot.services.database.utils import get_lessons_with_homework
from tgbot.services.kai_parser.utils import lesson_type_to_text, lesson_type_to_emoji


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

    msg = templates.schedule_day_template.format(
        day_of_week=templates.week_day.format(
            pointer='',
            day=_(messages.week_days[date.weekday()]),
            date=date.strftime("%d.%m.%Y")
        ),
        lessons='\n\n'.join(str_lessons) + '\n'
    )

    return msg


async def show_day_details(call: CallbackQuery, callback_data: dict):
    db, _ = call.bot.get('database'), call.bot.get('_')
    date = datetime.date.fromisoformat(callback_data['payload'])
    async with db() as session:
        tg_user = await session.get(User, call.from_user.id)
        lessons = await get_lessons_with_homework(session, tg_user.group_id, date)

    await call.message.edit_text(
        form_day_with_details(_, lessons, date, tg_user.use_emoji),
        reply_markup=inline_keyboards.get_details_keyboard(_, lessons, date)
    )
    await call.answer()


async def show_lesson_menu(call: CallbackQuery, callback_data: dict):
    db, _ = call.bot.get('database'), call.bot.get('_')
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
        start_time=lesson.start_time,
        homework=homework.description if homework else _(messages.no_homework)
    )
    keyboard = inline_keyboards.get_homework_keyboard(_, lesson.id, date, homework)

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


async def start_homework_add(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    await call.message.edit_text(_(messages.homework_input))  # TODO: cancel keyboard
    await state.update_data(main_call=call.to_python(), date=callback_data['date'], lesson_id=callback_data['lesson_id'])
    await states.Homework.waiting_for_homework.set()
    await call.answer()


async def start_homework_edit(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    await call.message.edit_text(_(messages.homework_input))  # TODO: cancel keyboard
    await state.update_data(main_call=call.to_python(), date=callback_data['date'], lesson_id=callback_data['lesson_id'])
    await states.Homework.waiting_for_homework.set()
    await call.answer()


async def get_homework(message: Message, state: FSMContext):
    homework_description = message.text
    db, _ = message.bot.get('database'), message.bot.get('_')
    state_data = await state.get_data()
    lesson_id = int(state_data['lesson_id'])
    date = datetime.date.fromisoformat(state_data['date'])
    main_call = CallbackQuery(**state_data['main_call'])

    async with db.begin() as session:
        homework = await Homework.get_by_lesson_and_date(session, lesson_id, date)
        if homework:
            homework.description = homework_description
        else:
            homework = Homework(
                description=homework_description,
                date=date,
                lesson_id=lesson_id
            )
            session.add(homework)

    await message.delete()
    await show_lesson_menu(main_call, {'lesson_id': lesson_id, 'date': date.isoformat()})
    await state.finish()


async def delete_homework(call: CallbackQuery, callback_data: dict):
    db, _ = call.bot.get('database'), call.bot.get('_')
    date = datetime.date.fromisoformat(callback_data['date'])
    async with db.begin() as session:
        homework = await Homework.get_by_lesson_and_date(session, int(callback_data['lesson_id']), date)
        if homework:
            await session.delete(homework)

    await show_lesson_menu(call, callback_data)


def register_details(dp: Dispatcher):
    dp.register_callback_query_handler(show_day_details, callbacks.schedule.filter(action='details'))
    dp.register_callback_query_handler(show_lesson_menu, callbacks.details.filter(action='show'))
    dp.register_callback_query_handler(start_homework_add, callbacks.details.filter(action='add'))
    dp.register_callback_query_handler(start_homework_edit, callbacks.details.filter(action='edit'))
    dp.register_callback_query_handler(delete_homework, callbacks.details.filter(action='delete'))

    dp.register_message_handler(get_homework, state=states.Homework.waiting_for_homework)
