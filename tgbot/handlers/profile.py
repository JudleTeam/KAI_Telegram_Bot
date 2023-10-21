from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils import markdown as md
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.keyboards import inline_keyboards
from tgbot.misc import states
from tgbot.misc.callbacks import Navigation
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User

router = Router()


@router.callback_query(Navigation.filter(F.to == Navigation.To.group_choose))
async def show_group_choose(call: CallbackQuery, callback_data: Navigation, state: FSMContext, _,
                            db: async_sessionmaker):
    async with db() as session:
        user = await session.get(User, call.from_user.id)

    group_name = md.hcode(user.group.group_name) if user.group else '❌'
    keyboard = inline_keyboards.get_group_choose_keyboard(_, user, 'profile', callback_data.payload)
    message = await call.message.edit_text(_(messages.group_choose).format(group_name=group_name), reply_markup=keyboard)

    await state.update_data(call=call.to_python(), main_message=message.to_python(), payload=callback_data.payload)
    await state.set_state(states.GroupChoose.waiting_for_group)

    await call.answer()


@router.callback_query(Navigation.filter(F.to == Navigation.To.verification))
async def show_verification(call: CallbackQuery, callback_data: Navigation, state: FSMContext, _, db: async_sessionmaker):
    await state.clear()

    async with db() as session:
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
        reply_markup=inline_keyboards.get_verification_keyboard(_, user, callback_data.payload)
    )
    await call.answer()


async def send_verification(message: Message, state: FSMContext, _, db: async_sessionmaker):
    state_data = await state.get_data()
    await state.clear()

    async with db() as session:
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


@router.callback_query(Navigation.filter(F.to == Navigation.To.settings))
async def show_settings(call: CallbackQuery, _, db: async_sessionmaker):
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
