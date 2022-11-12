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
    admin_ids: list[int]
    use_redis: bool


@dataclass
class I18N:
    domain: str
    base_dir: Path
    locales_dir: Path


@dataclass
class Miscellaneous:
    rate_limit: float
    block_time: int


@dataclass
class Config:
    bot: TelegramBot
    database: DatabaseConfig
    misc: Miscellaneous
    i18n: I18N


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        bot=TelegramBot(
            token=env.str('BOT_TOKEN'),
            admin_ids=list(map(int, env.list('ADMINS'))),
            use_redis=env.bool('USE_REDIS'),
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
            block_time=env.int('BLOCK_TIME')
        )
    )
