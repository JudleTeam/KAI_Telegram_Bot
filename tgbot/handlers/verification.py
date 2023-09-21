import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, ContentType, ReplyKeyboardRemove

from tgbot.handlers.profile import show_verification, send_verification
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc import states, callbacks
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User, Role, KAIUser
from tgbot.services.kai_parser import KaiParser
from tgbot.services.kai_parser.schemas import KaiApiError, BadCredentials
from tgbot.services.utils import add_full_user_to_db, verify_profile_with_phone


async def unlink_account(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    async with db_session.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.kai_user = None
        user.remove_role(roles.verified)
        user.remove_role(roles.authorized)
        user.remove_role(roles.group_leader)

    logging.info(f'[{call.from_user.id}]: Unlinked account')
    await call.answer(_(messages.account_unlinked))
    await show_verification(call, callback_data, state)


async def kai_logout(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    async with db_session.begin() as session:
        user = await session.get(User, call.from_user.id)
        user.kai_user.login = None
        user.kai_user.password = None
        user.remove_role(roles.group_leader)
        user.remove_role(roles.authorized)

    logging.info(f'[{call.from_user.id}]: KAI logout')

    await call.answer(_(messages.kai_logout))
    await show_verification(call, callback_data, state)


async def start_kai_login(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')

    await call.message.edit_text(_(messages.login_input),
                                 reply_markup=inline_keyboards.get_cancel_keyboard(_, 'verification', callback_data['payload']))
    await call.answer()

    await state.update_data(main_call=call.to_python(), payload=callback_data['payload'])
    await states.KAILogin.waiting_for_login.set()

    logging.info(f'[{call.from_user.id}]: Start KAI login')


async def get_user_login(message: Message, state: FSMContext):
    _ = message.bot.get('_')

    await message.delete()
    async with state.proxy() as data:
        main_call = CallbackQuery(**data['main_call'])
        data['login'] = message.text.strip()
        payload = data['payload']

    await main_call.message.edit_text(_(messages.password_input),
                                      reply_markup=inline_keyboards.get_cancel_keyboard(_, 'verification', payload))
    await states.KAILogin.next()


async def get_user_password(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    db = message.bot.get('database')
    state_data = await state.get_data()

    await message.delete()
    password = message.text.strip()
    async with state.proxy() as data:
        login = data['login']
        main_call = CallbackQuery(**data['main_call'])

    await main_call.message.edit_text(_(messages.authorization_process))

    keyboard = inline_keyboards.get_back_keyboard(_, 'verification', payload=state_data['payload'])
    try:
        user_data = await KaiParser.get_full_user_data(login, password)

    except KaiApiError as error:
        await main_call.message.edit_text(_(messages.kai_error), reply_markup=keyboard)
        logging.info(f'[{message.from_id}]: Got KAI error on login - {error}')

    except BadCredentials:
        await main_call.message.edit_text(_(messages.bad_credentials), reply_markup=keyboard)
        logging.info(f'[{message.from_id}]: Bad credentials')

    else:
        result = await add_full_user_to_db(user_data, login, password, message.from_id, db)
        if result:
            await main_call.message.edit_text(_(messages.success_login), reply_markup=keyboard)
            logging.info(f'[{message.from_id}]: Success login')
        else:
            await main_call.message.edit_text(_(messages.credentials_busy), reply_markup=keyboard)
            logging.info(f'[{message.from_id}]: Tried to login to someone else\'s account ({login})')

    await state.finish()


async def send_phone_keyboard(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')

    await states.PhoneSendState.waiting_for_phone.set()
    await state.update_data(payload=callback_data['payload'])
    await call.message.answer(_(messages.share_contact), reply_markup=reply_keyboards.get_send_phone_keyboard(_))
    await call.answer()


async def get_user_phone(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    db = message.bot.get('database')

    if message.from_id != message.contact.user_id:
        await message.answer(_(messages.not_your_phone))
        return

    is_verified = await verify_profile_with_phone(message.from_id, message.contact.phone_number, db)
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
        await send_verification(message, state)
    else:
        await message.answer(text, reply_markup=reply_keyboards.get_main_keyboard(_))


async def check_phone(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    async with db.begin() as session:
        user = await session.get(User, call.from_user.id)
        kai_user = await KAIUser.get_by_phone(user.phone, db)

        if not kai_user:
            await call.answer(_(messages.phone_not_found), show_alert=True)
            return

        if kai_user.telegram_user_id:
            await call.answer(_(messages.kai_account_busy), show_alert=True)
            return

        kai_user.telegram_user_id = call.from_user.id
        kai_user = await session.merge(kai_user)

        roles_dict = await Role.get_roles_dict(db)
        user.roles.append(roles_dict[roles.verified])
        if kai_user.password:
            user.roles.append(roles_dict[roles.authorized])

    await call.answer(_(messages.phone_found), show_alert=True)
    await show_verification(call, callback_data, state)


def register_verification(dp: Dispatcher):
    dp.register_callback_query_handler(start_kai_login, callbacks.action.filter(name='start_login'))
    dp.register_callback_query_handler(kai_logout, callbacks.action.filter(name='logout'))
    dp.register_callback_query_handler(unlink_account, callbacks.action.filter(name='unlink'))
    dp.register_message_handler(get_user_login, state=states.KAILogin.waiting_for_login)
    dp.register_message_handler(get_user_password, state=states.KAILogin.waiting_for_password)

    dp.register_callback_query_handler(send_phone_keyboard, callbacks.action.filter(name='send_phone'))
    dp.register_callback_query_handler(check_phone, callbacks.action.filter(name='check_phone'))
    dp.register_message_handler(get_user_phone, content_types=[ContentType.CONTACT], state=states.PhoneSendState.waiting_for_phone)
