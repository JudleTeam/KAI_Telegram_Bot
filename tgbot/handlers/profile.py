from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md
from aiogram.utils.exceptions import InvalidQueryID

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks, states
from tgbot.misc.texts import messages
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
    if (await state.get_state()) is None:
        await states.GroupChoose.waiting_for_group.set()


def register_profile(dp: Dispatcher):
    dp.register_callback_query_handler(show_group_choose, callbacks.navigation.filter(to='grp_choose'), state='*')
