from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils import markdown as md
from aiogram.utils.exceptions import InvalidQueryID

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks, states
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User


async def show_group_choose(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')
    async with db_session() as session:
        user = await session.get(User, call.from_user.id)

    group_name = md.hcode(user.group.group_name) if user.group else '❌'
    keyboard = inline_keyboards.get_group_choose_keyboard(_, user, 'profile', callback_data['payload'])
    message = await call.message.edit_text(_(messages.group_choose).format(group_name=group_name), reply_markup=keyboard)

    try:
        await call.answer()
    except InvalidQueryID:
        pass

    await state.update_data(call=call.to_python(), main_message=message.to_python(), payload=callback_data['payload'])
    await states.GroupChoose.waiting_for_group.set()


async def show_verification(call: CallbackQuery, callback_data: dict, state: FSMContext):
    _ = call.bot.get('_')
    db_session = call.bot.get('database')

    await state.finish()

    async with db_session() as session:
        user = await session.get(User, call.from_user.id)

    verified_status = '✅' if user.has_role(roles.verified) else '❌'
    phone_status = '✅' if user.phone else '❌'
    authorized_status = '✅' if user.has_role(roles.authorized) else '❌'

    await call.message.edit_text(
        _(messages.verification_menu).format(
            phone_status=phone_status,
            kai_status=authorized_status,
            profile_status=verified_status
        ),
        reply_markup=inline_keyboards.get_verification_keyboard(_, user, callback_data['payload'])
    )
    await call.answer()


async def send_verification(message: Message, state: FSMContext):
    _ = message.bot.get('_')
    db_session = message.bot.get('database')
    state_data = await state.get_data()
    await state.finish()

    async with db_session() as session:
        user = await session.get(User, message.from_id)

    verified_status = '✅' if user.has_role(roles.verified) else '❌'
    phone_status = '✅' if user.phone else '❌'
    authorized_status = '✅' if user.has_role(roles.authorized) else '❌'

    await message.answer(
        _(messages.verification_menu).format(
            phone_status=phone_status,
            kai_status=authorized_status,
            profile_status=verified_status
        ),
        reply_markup=inline_keyboards.get_verification_keyboard(_, user, state_data['payload'])
    )


async def show_settings(call: CallbackQuery):
    _, db = call.bot.get('_'), call.bot.get('database')

    async with db() as session:
        tg_user: User = await session.get(User, call.from_user.id)

    await call.message.edit_text(
        _(messages.settings).format(
            emoji_status='✅' if tg_user.use_emoji else '❌',
            teachers_status='✅' if tg_user.show_teachers_in_schedule else '❌'
        ),
        reply_markup=inline_keyboards.get_settings_keyboard(_, tg_user)
    )

    await call.answer()


def register_profile(dp: Dispatcher):
    dp.register_callback_query_handler(show_group_choose, callbacks.navigation.filter(to='grp_choose'), state='*')
    dp.register_callback_query_handler(show_verification, callbacks.navigation.filter(to='verification'), state='*')
    dp.register_callback_query_handler(show_settings, callbacks.navigation.filter(to='settings'))
