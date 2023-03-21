from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards
from tgbot.misc import callbacks
from tgbot.misc.texts import messages
from tgbot.services.database.models import User


async def show_classmates(call: CallbackQuery):
    _ = call.bot.get('_')
    db = call.bot.get('database')

    async with db() as session:
        user = await session.get(User, call.from_user.id)

    classmates = await user.kai_user.get_classmates(db)
    formatted_classmates = list()
    for member in classmates:
        name = member.full_name
        if member.telegram_user_id:
            member_tg = await call.bot.get_chat(call.from_user.id)
            if member_tg.mention:
                name = md.hlink(member.full_name, f't.me/{member_tg.mention[1:]}')

        prefix = member.prefix or ''

        formatted_member = f'{member.position}. {prefix} {name}'
        formatted_classmates.append(formatted_member)

    classmates_str = '\n'.join(formatted_classmates)

    await call.message.edit_text(
        _(messages.classmates_list).format(
            group_name=md.hcode(user.kai_user.group.group_name),
            classmates=classmates_str
        ),
        reply_markup=inline_keyboards.get_back_keyboard(_, 'my_group'),
        disable_web_page_preview=True
    )
    await call.answer()


def register_my_group(dp: Dispatcher):
    dp.register_callback_query_handler(show_classmates, callbacks.navigation.filter(to='classmates'))
