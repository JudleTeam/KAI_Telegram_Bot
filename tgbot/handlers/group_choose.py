import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from tgbot.handlers.profile import show_group_choose
from tgbot.misc import callbacks, states
from tgbot.misc.texts import messages
from tgbot.services.database.models import User, Group, GroupLesson
from tgbot.services.kai_parser.schemas import KaiApiError, ParsingError
from tgbot.services.kai_parser.utils import add_group_schedule


async def add_to_favorites(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    async with db_session.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.favorite_groups.append(user.group)

    logging.info(f'[{call.from_user.id}]: Add group {user.group.group_name} from favorites')
    await call.answer(_(messages.group_added))
    await show_group_choose(call, callback_data, state)


async def remove_from_favorites(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    async with db_session.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.favorite_groups.remove(user.group)

    logging.info(f'[{call.from_user.id}]: Remove group {user.group.group_name} from favorites')
    await call.answer(_(messages.group_removed))
    await show_group_choose(call, callback_data, state)


async def select_group(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    select_group_id = int(callback_data['id'])
    async with db_session() as session:
        user = await session.get(User, call.from_user.id)
        if user.group_id == select_group_id:
            await call.answer(_(messages.group_already_selected))
            return
        user.group_id = int(callback_data['id'])

        await session.commit()
        await session.refresh(user)

    logging.info(f'[{call.from_user.id}]: Changed group to {user.group.group_name} with favorite groups')
    async with db_session() as session:
        schedule = (await session.execute(select(GroupLesson).where(GroupLesson.group_id == user.group_id))).scalars().all()
        if not schedule:
            try:
                await add_group_schedule(user.group_id, db_session)
            except KaiApiError:
                logging.error(f'Error with kai api for group {user.group.group_name}')
                await call.answer(messages.kai_error)
            except ParsingError:
                logging.error(f'Error with parsing for group {user.group.group_name}')
                await call.answer(messages.base_error)
    await call.answer(_(messages.group_changed))
    await show_group_choose(call, callback_data, state)


async def get_group_name(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    group_name = message.text

    await message.delete()
    async with state.proxy() as data:
        main_mess = Message(**data['main_message'])
        call = CallbackQuery(**data['call'])

    db_session = message.bot.get('database')
    group = await Group.get_group_by_name(group_name, db_session)
    if not group:
        if _(messages.group_not_exist) not in main_mess.text:
            main_mess = await main_mess.edit_text(main_mess.text + '\n\n' + _(messages.group_not_exist),
                                                  reply_markup=main_mess.reply_markup)
            await state.update_data(main_message=main_mess.to_python())
        return

    async with db_session.begin() as session:
        user = await session.get(User, message.from_id)
        if user.group_id == group.group_id:
            return

        user.group_id = group.group_id

    logging.info(f'[{message.from_id}]: Changed group to {group_name} with input')
    async with db_session() as session:
        schedule = (await session.execute(select(GroupLesson).where(GroupLesson.group_id == user.group_id))).scalars().all()
        if not schedule:
            try:
                await add_group_schedule(user.group_id, db_session)
            except KaiApiError:
                logging.error(f'Error with kai api for group {group_name}')
                await call.answer(messages.kai_error)
            except ParsingError:
                logging.error(f'Error with parsing for group {group_name}')
                await call.answer(messages.base_error)
    await show_group_choose(call, {'payload': data['payload']}, state)


def register_group_choose(dp: Dispatcher):
    dp.register_callback_query_handler(add_to_favorites, callbacks.group_choose.filter(action='add'),
                                       state=states.GroupChoose.waiting_for_group)
    dp.register_callback_query_handler(remove_from_favorites, callbacks.group_choose.filter(action='remove'),
                                       state=states.GroupChoose.waiting_for_group)
    dp.register_callback_query_handler(select_group, callbacks.group_choose.filter(action='select'),
                                       state=states.GroupChoose.waiting_for_group)

    dp.register_message_handler(get_group_name, state=states.GroupChoose.waiting_for_group)
