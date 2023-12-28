import asyncio
import logging
import os
import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import I18n
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from tgbot.config import load_config, Config
from tgbot import handlers
from tgbot import filters
from tgbot import middlewares
from tgbot.services.database.models import Role
from tgbot.services.database.models.right import Right
from tgbot.services.kai_parser.utils import parse_all_groups, parse_all_groups_schedule

logger = logging.getLogger(__name__)


def register_all_middlewares(dp: Dispatcher, config: Config):
    i18n = I18n(path=config.i18n.locales_dir, default_locale='en', domain=config.i18n.domain)
    middleware = middlewares.CacheAndDatabaseI18nMiddleware(i18n)
    dp.update.middleware(middleware)

    user_checker = middlewares.UserCheckerMiddleware()
    dp.callback_query.middleware(user_checker)
    dp.message.middleware(user_checker)

    bot_typing_middleware = middlewares.BotTypingMiddleware()
    dp.message.middleware(bot_typing_middleware)


def register_all_filters(dp):
    for aiogram_filter in filters.filters:
        dp.filters_factory.bind(aiogram_filter)


def start_jobs(db):
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    scheduler.add_job(
        func=parse_all_groups_schedule,
        trigger='cron',
        hour=3,
        kwargs={
            'db': db
        }
    )

    scheduler.add_job(
        func=parse_all_groups,
        trigger='cron',
        hour=2,
        minute=30,
        kwargs={
            'db': db
        }
    )

    scheduler.start()


async def main():
    config = load_config('.env')

    log_file = rf'logs/{datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")}.log'
    if not os.path.exists('logs'):
        os.mkdir('logs')

    if config.misc.write_logs:
        log_handlers = logging.FileHandler(log_file), logging.StreamHandler()
    else:
        log_handlers = logging.StreamHandler(),

    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
        handlers=log_handlers
    )

    engine = create_async_engine(config.database.url, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    redis = Redis(db=config.redis.db)
    storage = RedisStorage(redis=redis)
    bot = Bot(token=config.bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)

    register_all_middlewares(dp, config)
    dp.include_routers(*handlers.routers)

    await Right.insert_default_rights(async_session)
    await Role.insert_default_roles(async_session)

    start_jobs(async_session)

    await dp.start_polling(
        bot,
        config=config,
        redis=redis,
        db=async_session,
        log_file=log_file
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error('Bot stopped!')
        raise e
