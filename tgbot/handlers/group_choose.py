import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.profile import show_group_choose
from tgbot.misc import states
from tgbot.misc.callbacks import Group as GroupCallback, Navigation
from tgbot.misc.texts import messages
from tgbot.services.database.models import User, Group


router = Router()

@router.callback_query(GroupCallback.filter(F.action == GroupCallback.Action.add))
async def add_to_favorites(call: CallbackQuery, callback_data: GroupCallback, state: FSMContext, _,
                           db: async_sessionmaker):
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.favorite_groups.append(user.group)

    logging.info(f'[{call.from_user.id}]: Add group {user.group.group_name} from favorites')
    await call.answer(_(messages.group_added))
    await show_group_choose(call, Navigation(to=Navigation.To.group_choose, payload=callback_data.payload), state)


@router.callback_query(GroupCallback.filter(F.action == GroupCallback.Action.remove))
async def remove_from_favorites(call: CallbackQuery, callback_data: GroupCallback, state: FSMContext, _,
                                db: async_sessionmaker):
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.favorite_groups.remove(user.group)

    logging.info(f'[{call.from_user.id}]: Remove group {user.group.group_name} from favorites')
    await call.answer(_(messages.group_removed))
    await show_group_choose(call, Navigation(to=Navigation.To.group_choose, payload=callback_data.payload), state)


@router.callback_query(GroupCallback.filter(F.action == GroupCallback.Action.select))
async def select_group(call: CallbackQuery, callback_data: GroupCallback, state: FSMContext, _, db: async_sessionmaker):
    async with db() as session:
        user = await session.get(User, call.from_user.id)
        if user.group_id == callback_data.id:
            await call.answer(_(messages.group_already_selected))
            return
        user.group_id = callback_data.id

        await session.commit()
        await session.refresh(user)

    logging.info(f'[{call.from_user.id}]: Changed group to {user.group.group_name} with favorite groups')
    await call.answer(_(messages.group_changed))
    await show_group_choose(call, Navigation(to=Navigation.To.group_choose, payload=callback_data.payload), state)


@router.message(states.GroupChoose.waiting_for_group)
async def get_group_name(message: Message, state: FSMContext, _, db: async_sessionmaker):
    group_name = message.text

    await message.delete()
    state_data = await state.get_data()
    main_mess = Message(**state_data['main_message'])
    call = CallbackQuery(**state_data['call'])

    async with db.begin() as session:
        group = await Group.get_group_by_name(session, group_name)
        if not group:
            if _(messages.group_not_exist) not in main_mess.text:
                main_mess = await main_mess.edit_text(main_mess.text + '\n\n' + _(messages.group_not_exist),
                                                      reply_markup=main_mess.reply_markup)
                await state.update_data(main_message=main_mess.to_python())
            return

        user = await session.get(User, message.from_id)
        if user.group_id == group.group_id:
            return

        user.group_id = group.group_id

    logging.info(f'[{message.from_id}]: Changed group to {group_name} with input')
    await show_group_choose(call, Navigation(to=Navigation.To.group_choose, payload=state_data['payload']), state)
