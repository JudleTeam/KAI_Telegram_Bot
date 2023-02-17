from typing import Sequence

from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from iso_language_codes import language_dictionary

from tgbot.services.database.base import Base


class User(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    language_id = Column(Integer, ForeignKey('language.id'), nullable=True)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=text('NOW()'))
    is_blocked_bot = Column(Boolean, nullable=False, server_default=text('false'))
    is_blocked = Column(Boolean, nullable=False, server_default=text('false'))

    language = relationship('Language', lazy='selectin', backref='user')
    role = relationship('Role', lazy='selectin', backref='user')


class Language(Base):
    __tablename__ = 'language'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(20), nullable=False)
    code = Column(String(2), unique=True, nullable=False)
    is_available = Column(Boolean, server_default=text('true'))

    @classmethod
    async def get_available_languages(cls, db_session):
        async with db_session() as session:
            records = await session.execute(select(Language).where(Language.is_available == True))
            return records.scalars().all()

    @classmethod
    async def check_languages(cls, db_session, locales: Sequence):
        languages = language_dictionary()
        new_locales = list(locales)
        async with db_session.begin() as session:
            records = await session.execute(select(Language))
            database_locales = records.scalars().all()

            # Language availability check
            for database_locale in database_locales:
                if database_locale.code not in locales:
                    database_locale.is_available = False
                else:
                    new_locales.remove(database_locale.code)

            # Adding new languages
            for locale in new_locales:
                new_locale = Language(
                    title=languages[locale]['Autonym'],
                    code=locale
                )
                session.add(new_locale)


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(40), nullable=False)
