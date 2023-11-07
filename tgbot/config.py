from os import environ
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from sqlalchemy import URL


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: URL


class RedisConfig(BaseModel):
    db: int


class TelegramBot(BaseModel):
    token: str
    admin_ids: set[int]
    main_admins_ids: set[int]


class I18N(BaseModel):
    domain: str
    base_dir: Path
    locales_dir: Path


class Miscellaneous(BaseModel):
    write_logs: bool
    channel_link: str
    contact_link: str
    donate_link: str
    guide_link: str


class Config(BaseModel):
    bot: TelegramBot
    database: DatabaseConfig
    misc: Miscellaneous
    i18n: I18N
    redis: RedisConfig


def load_config(path: str = None):
    load_dotenv(dotenv_path=path)

    main_admins = set(map(int, environ.get('MAIN_ADMINS', '').split(',')))
    admins = set(map(int, environ.get('ADMINS', '').split(','))) | main_admins

    db_url = URL.create(
        drivername='postgresql+asyncpg',
        username=environ.get('DB_USER'),
        password=environ.get('DB_PASS'),
        host=environ.get('DB_HOST', '127.0.0.1'),
        port=environ.get('DB_PORT', 5432),
        database=environ.get('DB_NAME')
    )

    return Config(
        bot=TelegramBot(
            token=environ.get('BOT_TOKEN'),
            admin_ids=admins,
            main_admins_ids=main_admins
        ),
        database=DatabaseConfig(
            url=db_url
        ),
        i18n=I18N(
            domain=environ.get('I18N_DOMAIN'),
            base_dir=Path(__file__).parent,
            locales_dir=Path(__file__).parent / 'locales'
        ),
        misc=Miscellaneous(
            write_logs=environ.get('WRITE_LOGS', True),
            channel_link=environ.get('CHANNEL_LINK'),
            contact_link=environ.get('CONTACT_LINK'),
            donate_link=environ.get('DONATE_LINK'),
            guide_link=environ.get('GUIDE_LINK')
        ),
        redis=RedisConfig(
            db=environ.get('REDIS_DB', 0)
        )
    )
