import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils import markdown as md
from aiogram.utils.deep_linking import decode_payload
from aiogram.utils.i18n import gettext as _
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.config import Config
from tgbot.handlers.profile import send_verification
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.middlewares.language import CacheAndDatabaseI18nMiddleware
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User, Role



router = Router()

@router.message(CommandStart())
async def command_start(message: Message, db: async_sessionmaker, redis: Redis, config: Config,
                        i18n: CacheAndDatabaseI18nMiddleware):
    # TODO: update work with deep link
    # args = message.get_args()
    # try:
    #     payload = decode_payload(args)
    # except UnicodeDecodeError:
    #     payload = None

    async with db.begin() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            roles_dict = await Role.get_roles_dict(db)
            locale = await i18n.get_user_locale(message.from_user.id, redis, db)
            user = User(telegram_id=message.from_user.id, source='', roles=[roles_dict[roles.student]], language=locale)
            session.add(user)
            await session.commit()

            await redis.set(name=f'{message.from_id}:exists', value='', ex=3600)

            # Need update with new lang system
            if language:
                welcome = _(messages.language_found).format(language=language.title)
            else:
                welcome = messages.language_not_found

            await state.update_data(payload='at_start')
            await message.answer(welcome)
            await send_verification(message, state)
            logging.info(f'New user: {message.from_user.mention} {message.from_user.full_name} [{message.from_id}]')
        else:
            await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())


@router.message(Command('menu'))
async def command_menu(message: Message, state: FSMContext):
    await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())
    await state.clear()
