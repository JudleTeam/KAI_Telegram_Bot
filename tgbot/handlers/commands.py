import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils import markdown as md
from aiogram.utils.deep_linking import decode_payload

from tgbot.config import Config
from tgbot.handlers.profile import send_verification
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User, Role, Language


async def command_start(message: Message, state: FSMContext):
    db = message.bot.get('database')
    _ = message.bot.get('_')

    args = message.get_args()
    try:
        payload = decode_payload(args)
    except UnicodeDecodeError:
        payload = None

    async with db() as session:
        user = await session.get(User, message.from_id)
        if not user:
            redis = message.bot.get('redis')
            roles_dict = await Role.get_roles_dict(db)
            language = await Language.get_by_code(session, str(message.from_user.locale))
            user = User(telegram_id=message.from_id, source=payload, roles=[roles_dict[roles.student]],
                        language=language)
            session.add(user)
            await session.commit()

            if language:
                _.ctx_locale.set(language.code)
                await redis.set(name=f'{message.from_id}:lang', value=language.code)

            await redis.set(name=f'{message.from_id}:exists', value='1')

            config: Config = message.bot.get('config')
            start_guide = (
                f'Перед началом использования бота настоятельно рекомендуем ознакомиться с {md.hlink("инструкцией", config.misc.guide_link)}. '
                'В случае чего её можно будет посмотреть позже\n\n'
                '---\n\n'
                f'Before starting to use the bot, we strongly recommend that you read {md.hlink("guide", config.misc.guide_link)}. '
                'If something happens, you can watch it later\n\n'
            )

            await message.answer(start_guide)

            if language:
                welcome = _(messages.language_found).format(language=language.title)
            else:
                welcome = messages.language_not_found

            await state.update_data(payload='at_start')
            await message.answer(welcome)
            await send_verification(message, state)
            logging.info(f'New user: {message.from_user.mention} {message.from_user.full_name} [{message.from_id}]')
        else:
            await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))


async def command_menu(message: Message, state: FSMContext):
    _ = message.bot.get('_')

    await message.answer(_(messages.main_menu), reply_markup=reply_keyboards.get_main_keyboard(_))
    await state.finish()


def register_commands(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(command_menu, commands=['menu'], state='*')
