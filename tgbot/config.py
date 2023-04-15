from dataclasses import dataclass
from pathlib import Path

from environs import Env


@dataclass
class DatabaseConfig:
    host: str
    password: str
    user: str
    database: str
    port: int


@dataclass
class TelegramBot:
    token: str
    admin_ids: set[int]
    main_admins_ids: set[int]
    use_redis: bool


@dataclass
class I18N:
    domain: str
    base_dir: Path
    locales_dir: Path


@dataclass
class Miscellaneous:
    rate_limit: float
    write_logs: bool
    channel_link: str
    contact_link: str


@dataclass
class Config:
    bot: TelegramBot
    database: DatabaseConfig
    misc: Miscellaneous
    i18n: I18N


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    main_admins = set(map(int, env.list('MAIN_ADMINS')))
    admins = set(map(int, env.list('ADMINS'))) | main_admins

    return Config(
        bot=TelegramBot(
            token=env.str('BOT_TOKEN'),
            admin_ids=admins,
            main_admins_ids=main_admins,
            use_redis=env.bool('USE_REDIS')
        ),
        database=DatabaseConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME'),
            port=env.int('DB_PORT')
        ),
        i18n=I18N(
            domain=env.str('I18N_DOMAIN'),
            base_dir=Path(__file__).parent,
            locales_dir=Path(__file__).parent / 'locales'
        ),
        misc=Miscellaneous(
            rate_limit=env.float('RATE_LIMIT'),
            write_logs=env.bool('WRITE_LOGS'),
            channel_link=env.str('CHANNEL_LINK'),
            contact_link=env.str('CONTACT_LINK')
        )
    )
