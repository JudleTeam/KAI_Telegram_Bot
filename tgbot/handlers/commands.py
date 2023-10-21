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
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User, Role



router = Router()

@router.message(CommandStart())
async def command_start(message: Message, db: async_sessionmaker, redis: Redis, config: Config):
    # TODO: update work with deep link
    args = message.get_args()
    try:
        payload = decode_payload(args)
    except UnicodeDecodeError:
        payload = None

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
            user = User(telegram_id=message.from_user.id, source=payload, roles=[roles_dict[roles.student]])
            session.add(user)

            await redis.set(name=f'{message.from_user.id}:exists', value='1')

            start_guide = (
                f'Перед началом использования бота настоятельно рекомендуем ознакомиться с {md.hlink("инструкцией", config.misc.guide_link)}. '
                'В случае чего её можно будет посмотреть позже\n\n'
                '---\n\n'
                f'Before starting to use the bot, we strongly recommend that you read {md.hlink("guide", config.misc.guide_link)}. '
                'If something happens, you can watch it later\n\n'
            )

            await message.answer(start_guide)

            await message.answer(_(messages.welcome), reply_markup=inline_keyboards.get_start_keyboard(_))
            logging.info(f'New user: {message.from_user.mention} {message.from_user.full_name} [{message.from_user.id}]')
        else:
            await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())


@router.message(Command('menu'))
async def command_menu(message: Message, state: FSMContext):
    await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard())
    await state.clear()
