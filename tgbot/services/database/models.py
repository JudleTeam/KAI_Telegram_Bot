from sqlalchemy import Column, BigInteger

from tgbot.services.database.base import Base


class User(Base):
    __tablename__ = 'user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
