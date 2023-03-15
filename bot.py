import asyncio
import logging
import os
import datetime

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aioredis import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from tgbot.config import load_config
from tgbot import handlers
from tgbot import filters
from tgbot import middlewares
from tgbot.services.database.base import Base
from tgbot.services.database.models import Language, Role
from tgbot.services.database.models.right import Right
from tgbot.services.kai_parser import KaiParser
from tgbot.services.kai_parser.utils import parse_groups

logger = logging.getLogger(__name__)


def register_all_middlewares(dp, config):
    dp.setup_middleware(middlewares.EnvironmentMiddleware(config=config))
    dp.setup_middleware(middlewares.ThrottlingMiddleware(limit=config.misc.rate_limit))
    dp.setup_middleware(middlewares.UserCheckerMiddleware())

    i18n = middlewares.ACLMiddleware(config.i18n.domain, config.i18n.locales_dir)
    dp.bot['_'] = i18n
    dp.setup_middleware(i18n)


def register_all_filters(dp):
    for aiogram_filter in filters.filters:
        dp.filters_factory.bind(aiogram_filter)


def register_all_handlers(dp):
    for register in handlers.register_functions:
        register(dp)


async def main():
    log_file = rf'logs/{datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")}.log'
    if not os.path.exists('logs'): os.mkdir('logs')
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
        handlers=(logging.FileHandler(log_file), logging.StreamHandler())
    )
    logger.info('Starting bot')
    config = load_config('.env')

    engine = create_async_engine(
        f'postgresql+asyncpg://{config.database.user}:{config.database.password}@'
        f'{config.database.host}:{config.database.port}/{config.database.database}',
        future=True
    )
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async_sessionmaker = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    storage = RedisStorage2() if config.bot.use_redis else MemoryStorage()
    redis = Redis()
    bot = Bot(token=config.bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    bot_info = await bot.me
    logger.info(f'Bot: {bot_info.username} [{bot_info.mention}]')

    bot['config'] = config
    bot['redis'] = redis
    bot['database'] = async_sessionmaker

    register_all_middlewares(dp, config)
    register_all_filters(dp)
    register_all_handlers(dp)

    await Language.check_languages(async_sessionmaker, bot['_'].available_locales)
    await Right.insert_default_rights(async_sessionmaker)
    await Role.insert_default_roles(async_sessionmaker)
    await parse_groups(await KaiParser.get_group_ids(), async_sessionmaker)

    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()

        bot_session = await bot.get_session()
        await bot_session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error('Bot stopped!')
        raise e
