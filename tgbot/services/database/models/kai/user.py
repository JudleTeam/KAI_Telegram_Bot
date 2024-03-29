import os

from dotenv import load_dotenv
from sqlalchemy import Integer, Column, BigInteger, ForeignKey, String, Date, Boolean
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType

from tgbot.services.database.base import Base

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')


class KAIUser(Base):
    __tablename__ = 'kai_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    kai_id = Column(Integer, unique=True, nullable=True)

    telegram_user_id = Column(BigInteger, ForeignKey('telegram_user.telegram_id'), unique=True)

    position = Column(Integer, nullable=True)
    prefix = Column(String(32), nullable=True)
    login = Column(String(64), unique=True, nullable=True)
    password = Column(StringEncryptedType(key=SECRET_KEY), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=True, unique=False)  # БЫВАЕТ ЧТО У ДВУХ ЛЮДЕЙ ОДИН И ТОТ ЖЕ НОМЕР!!!
    email = Column(String(64), nullable=False, unique=True)
    sex = Column(String(16), nullable=True)  # Потом вынести типы в отдельную таблицу
    birthday = Column(Date, nullable=True)
    is_leader = Column(Boolean, nullable=False)

    group_id = Column(BigInteger, ForeignKey('group.group_id', name='fk_kai_user_group'), nullable=False)
    zach_number = Column(String(32), nullable=True)  # Уникальный?
    competition_type = Column(String(64), nullable=True)  # Потом вынести типы в отдельную таблицу
    contract_number = Column(BigInteger, nullable=True)  # Уникальный?
    edu_level = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    edu_cycle = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    edu_qualification = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    program_form = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    status = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу

    group = relationship('Group', lazy='selectin', foreign_keys=[group_id])
    telegram_user = relationship('User', lazy='selectin', uselist=False, back_populates='kai_user')

    async def get_classmates(self, db: async_sessionmaker):
        async with db() as session:
            records = await session.execute(select(KAIUser).where(KAIUser.group_id == self.group_id).order_by(KAIUser.position))

        return records.scalars().all()

    @property
    def is_logged_in(self) -> bool:
        return bool(self.kai_id)

    @classmethod
    async def get_by_phone(cls, phone: str, db: async_sessionmaker):
        async with db() as session:
            records = await session.execute(select(KAIUser).where(KAIUser.phone == phone))

        return records.scalars().all()

    @classmethod
    async def get_by_email(cls, session, email: str):
        record = await session.execute(select(KAIUser).where(KAIUser.email == email))

        return record.scalar()

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int, db: async_sessionmaker):
        async with db() as session:
            record = await session.execute(select(KAIUser).where(KAIUser.telegram_user_id == telegram_id))

        return record.scalar()
