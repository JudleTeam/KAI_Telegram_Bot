from sqlalchemy import Column, Integer, String

from tgbot.services.database.base import Base


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(40), nullable=False)
