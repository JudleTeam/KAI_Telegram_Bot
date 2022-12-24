from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from sqlalchemy import select

from tgbot.services.database.models import User
from tgbot.misc import messages


class UserCheckerMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.text == '/start':
            return

        db_session = message.bot.get('database')
        _ = message.bot.get('_')
        redis = message.bot.get('redis')

        cached_is_user_exists = await redis.get(f'{message.from_id}:exists')
        cached_is_user_blocked = await redis.get(f'{message.from_id}:blocked')
        if cached_is_user_exists is None or cached_is_user_blocked is None:
            async with db_session() as session:
                stmt = select(User).where(User.telegram_id == message.from_id)
                database_user = (await session.execute(stmt)).scalar()
                if database_user:
                    await redis.set(name=f'{message.from_id}:exists', value='1')
                    blocked_value = '1' if database_user.is_blocked else ''
                    await redis.set(name=f'{message.from_id}:blocked', value=blocked_value)
                else:
                    await redis.set(name=f'{message.from_id}:exists', value='')
        else:
            if not cached_is_user_exists:
                await message.answer(_(messages.user_unregistered))
                raise CancelHandler()

            if cached_is_user_blocked:
                await message.answer(_(messages.user_blocked))
                raise CancelHandler()

            return

        if not database_user:
            await message.answer(_(messages.user_unregistered))
            raise CancelHandler()
        
        if database_user.is_blocked:
            await message.answer(_(messages.user_blocked))
            raise CancelHandler()
