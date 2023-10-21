from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.keyboards import inline_keyboards
from tgbot.misc.callbacks import Navigation
from tgbot.misc.texts import roles, messages
from tgbot.services.database.models import User

router = Router()


@router.callback_query(Navigation.filter(F.to == Navigation.To.my_group))
async def show_my_group(call: CallbackQuery, _, db: async_sessionmaker):
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
