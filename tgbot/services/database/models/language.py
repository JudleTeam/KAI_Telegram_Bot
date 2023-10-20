from typing import Sequence, Optional

from iso_language_codes import language_dictionary
from sqlalchemy import Column, Integer, Boolean, String, text
from sqlalchemy.future import select

from tgbot.services.database.base import Base


class Language(Base):
    __tablename__ = 'language'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(20), nullable=False)
    code = Column(String(2), unique=True, nullable=False)
    is_available = Column(Boolean, server_default=text('true'))

    @classmethod
    async def get_by_code(cls, session, code: str) -> Optional['Language']:
        if code is None:
            return
        record = await session.execute(select(Language).where(Language.code == code))
        return record.scalar()

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
