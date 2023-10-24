import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.payload import decode_payload
from iso_language_codes import language_autonym
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from tgbot.handlers.profile import send_verification
from tgbot.keyboards import reply_keyboards
from tgbot.middlewares.language import CacheAndDatabaseI18nMiddleware
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User, Role



router = Router()

@router.message(CommandStart(deep_link_encoded=True))
@router.message(CommandStart())
async def command_start(message: Message, db: async_sessionmaker, redis: Redis, command: CommandObject, state: FSMContext,
                        i18n_middleware: CacheAndDatabaseI18nMiddleware):
    payload = None
    if command.args:
        try:
            payload = decode_payload(command.args)
        except UnicodeDecodeError:
            pass

    await message.answer(
        '‼️ Этот бот для БЕТА и ЭКСПЕРЕМЕНТАЛЬНЫХ версий КАИ бота! ‼️\n\n'
        'Он нужен для тестирования нового или экспериментального функционала и получения обратной связи. '
        'В этом боте может быть гораздо больше ошибок и проблем!\n'
        'Если вас это не интересует, лучше использовать основного бота - @kai_pup_bot\n\n'
        'Если нашли какую-то проблему или у вас есть отличное предложение, пишите - @printeromg\n\n'
        '‼️ Этот бот для БЕТА и ЭКСПЕРЕМЕНТАЛЬНЫХ версий КАИ бота! ‼️'
    )

    async with db.begin() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            roles_dict = await Role.get_roles_dict(db)
            locale = message.from_user.language_code

            if locale:
                welcome = _(messages.language_found).format(language=language_autonym(locale))
            else:
                welcome = messages.language_not_found
                locale = i18n_middleware.i18n.default_locale

            user = User(telegram_id=message.from_user.id, source=payload, roles=[roles_dict[roles.student]],
                        language=locale)
            session.add(user)
            await session.commit()

            await redis.set(name=f'{message.from_user.id}:exists', value='', ex=3600)

            await state.update_data(payload='at_start')
            await message.answer(welcome)
            await send_verification(message, state, db)
            logging.info(
                f'New user: {message.from_user.username} {message.from_user.full_name} [{message.from_user.id}] | Payload - {payload}'
            )
        else:
            await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())


@router.message(Command('menu'))
async def command_menu(message: Message, state: FSMContext):
    await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())
    await state.clear()
