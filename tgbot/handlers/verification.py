import json
import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ContentType, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.profile import show_verification, send_verification
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc import states
from tgbot.misc.callbacks import Action, Navigation
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User
from tgbot.services.kai_parser import KaiParser
from tgbot.services.kai_parser.schemas import KaiApiError, BadCredentials
from tgbot.services.utils import add_full_user_to_db, verify_profile_with_phone

router = Router()


@router.callback_query(Action.filter(F.name == Action.Name.unlink_account))
async def unlink_account(call: CallbackQuery, callback_data: Action, state: FSMContext, db: async_sessionmaker):
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.kai_user = None
        user.remove_role(roles.verified)
        user.remove_role(roles.authorized)
        user.remove_role(roles.group_leader)

    logging.info(f'[{call.from_user.id}]: Unlinked account')
    await call.answer(_(messages.account_unlinked))
    await show_verification(call, callback_data, state, db)


@router.callback_query(Action.filter(F.name == Action.Name.kai_logout))
async def kai_logout(call: CallbackQuery, callback_data: Action, state: FSMContext, db: async_sessionmaker):
    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.kai_user.login = None
        user.kai_user.password = None
        user.remove_role(roles.group_leader)
        user.remove_role(roles.authorized)

    logging.info(f'[{call.from_user.id}]: KAI logout')

    await call.answer(_(messages.kai_logout))
    await show_verification(call, callback_data, state, db)


@router.callback_query(Action.filter(F.name == Action.Name.start_kai_login))
async def start_kai_login(call: CallbackQuery, callback_data: Action, state: FSMContext):
    await call.message.edit_text(
        _(messages.login_input),
        reply_markup=inline_keyboards.get_cancel_keyboard(Navigation.To.verification, callback_data.payload)
    )
    await call.answer()

    await state.update_data(main_call=call.model_dump_json(), payload=callback_data.payload)
    await state.set_state(states.KAILogin.waiting_for_login)

    logging.info(f'[{call.from_user.id}]: Start KAI login')


@router.message(states.KAILogin.waiting_for_login)
async def get_user_login(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    state_data = await state.get_data()
    main_call = CallbackQuery(**json.loads(state_data['main_call']))
    await state.update_data(login=message.text.strip())
    payload = state_data['payload']

    main_call.message.as_(bot)
    await main_call.message.edit_text(
        _(messages.password_input),
        reply_markup=inline_keyboards.get_cancel_keyboard(Navigation.To.verification, payload)
    )
    await state.set_state(states.KAILogin.waiting_for_password)


@router.message(states.KAILogin.waiting_for_password)
async def get_user_password(message: Message, state: FSMContext, db: async_sessionmaker, bot: Bot):
    await message.delete()
    password = message.text.strip()
    state_data = await state.get_data()
    login = state_data['login']
    main_call = CallbackQuery(**json.loads(state_data['main_call']))

    main_call.message.as_(bot)
    await main_call.message.edit_text(_(messages.authorization_process))

    keyboard = inline_keyboards.get_back_keyboard(Navigation.To.verification, payload=state_data['payload'])
    # Привести это в порядок надо бы
    try:
        try:
            user_data = await KaiParser.get_full_user_data(login, password)

        except KaiApiError as error:
            await main_call.message.edit_text(_(messages.kai_error), reply_markup=keyboard)
            logging.info(f'[{message.from_user.id}]: Got KAI error on login - {error}')

        except BadCredentials:
            await main_call.message.edit_text(_(messages.bad_credentials), reply_markup=keyboard)
            logging.info(f'[{message.from_user.id}]: Bad credentials')

        else:
            is_available = await add_full_user_to_db(user_data, login, password, message.from_user.id, db)
            if is_available:
                await main_call.message.edit_text(_(messages.success_login), reply_markup=keyboard)
                logging.info(f'[{message.from_user.id}]: Success login')
            else:
                await main_call.message.edit_text(_(messages.credentials_busy), reply_markup=keyboard)
                logging.info(f'[{message.from_user.id}]: Tried to login to someone else\'s account ({login})')

    except Exception as error:
        await main_call.message.edit_text(_(messages.base_error))
        logging.error(f'[{message.from_user.id}]: Everything broke during login - {error}')

    await state.clear()


@router.callback_query(Action.filter(F.name == Action.Name.send_phone))
async def send_phone_keyboard(call: CallbackQuery, callback_data: Action, state: FSMContext):
    await state.set_state(states.PhoneSendState.waiting_for_phone)
    await state.update_data(payload=callback_data.payload)
    await call.message.answer(_(messages.share_contact), reply_markup=reply_keyboards.get_send_phone_keyboard())
    await call.answer()


@router.message(states.PhoneSendState.waiting_for_phone, F.content_type == ContentType.CONTACT)
async def get_user_phone(message: Message, state: FSMContext, db: async_sessionmaker):
    if message.from_user.id != message.contact.user_id:
        await message.answer(_(messages.not_your_phone))
        return

    is_verified = await verify_profile_with_phone(message.from_user.id, message.contact.phone_number, db)
    text = _(messages.phone_verified) + '\n\n'
    if is_verified is None:
        text += _(messages.kai_account_busy)
    elif is_verified:
        text += _(messages.phone_found)
    else:
        text += _(messages.phone_not_found)

    state_data = await state.get_data()
    if state_data['payload'] == 'at_start':
        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        await send_verification(message, state, db)
    else:
        await message.answer(text, reply_markup=reply_keyboards.get_main_keyboard())


@router.callback_query(Action.filter(F.name == Action.Name.check_phone))
async def check_phone(call: CallbackQuery, callback_data: dict, state: FSMContext, db: async_sessionmaker):
    async with db() as session:
        user = await session.get(User, call.from_user.id)

    is_verified = await verify_profile_with_phone(call.from_user.id, user.phone, db)

    if is_verified is None:
        await call.answer(_(messages.kai_account_busy), show_alert=True)
        return

    if is_verified:
        await call.answer(_(messages.phone_found), show_alert=True)
        await show_verification(call, callback_data, state, db)
    else:
        await call.answer(_(messages.phone_not_found), show_alert=True)
