from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks
from tgbot.misc.texts import roles, messages
from tgbot.services.database.models import User


async def show_my_group(call: CallbackQuery):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    async with db() as session:
        user = await session.get(User, call.from_user.id)
        if not user.has_role(roles.verified):
            await call.answer(_(messages.need_be_verified), show_alert=True)
            return

    pinned_text = user.kai_user.group.pinned_text or _(messages.missing)
    await call.message.edit_text(
        _(messages.my_group_menu).format(
            year=md.hcode(str(user.kai_user.group.group_name)[1]),
            faculty=md.hcode(str(user.kai_user.group.group_name)[0]),
            institute=md.hcode(user.kai_user.institute.name),
            departament=md.hcode(user.kai_user.departament.name),
            speciality=md.hcode(user.kai_user.speciality.code),
            profile=md.hcode(user.kai_user.profile.name),
            group_name=md.hcode(user.kai_user.group.group_name),
            pinned_text=md.hitalic(pinned_text)
        ),
        reply_markup=inline_keyboards.get_my_group_keyboard(_, user)
    )
    await call.answer()


def register_education(dp: Dispatcher):
    dp.register_callback_query_handler(show_my_group, callbacks.navigation.filter(to='my_group'))
