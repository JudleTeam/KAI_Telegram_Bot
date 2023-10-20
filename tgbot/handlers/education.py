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

    group = user.kai_user.group
    pinned_text = group.pinned_text or _(messages.missing)

    if str(group.group_name).startswith('8'):
        faculty = '1 | Технический колледж'
    else:
        faculty = str(group.group_name)[0]

    if len(str(group.group_name)) != 4:
        text = _(messages.unknown_group).format(pinned_text=md.hitalic(pinned_text))
    else:
        inst_add = ' (ВШПИТ)' if group.group_name in (6110, 6111, 6210, 6310) else ''
        text = _(messages.my_group_menu).format(
            year=md.hcode(str(group.group_name)[1]),
            faculty=md.hcode(faculty),
            institute=md.hcode(group.institute.name + inst_add),
            departament=md.hcode(group.departament.name),
            speciality=md.hcode(group.speciality.code),
            profile=md.hcode(group.profile.name),
            group_name=md.hcode(group.group_name),
            pinned_text=md.hitalic(pinned_text)
        )

    await call.message.edit_text(text, reply_markup=inline_keyboards.get_my_group_keyboard(_, user))

    await call.answer()


def register_education(dp: Dispatcher):
    dp.register_callback_query_handler(show_my_group, callbacks.navigation.filter(to='my_group'))
