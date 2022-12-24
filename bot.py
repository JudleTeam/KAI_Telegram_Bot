import asyncio
import logging

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
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info('Starting bot')
    config = load_config('.env')

    engine = create_async_engine(
        f'postgresql+asyncpg://{config.database.user}:{config.database.password}@'
        f'{config.database.host}:{config.database.port}/{config.database.database}',
        future=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_sessionmaker = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    storage = RedisStorage2() if config.bot.use_redis else MemoryStorage()
    redis = Redis()
    bot = Bot(token=config.bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    bot['config'] = config
    bot['redis'] = redis
    bot['database'] = async_sessionmaker

    register_all_middlewares(dp, config)
    register_all_filters(dp)
    register_all_handlers(dp)

    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error('Bot stopped!')
        raise e
