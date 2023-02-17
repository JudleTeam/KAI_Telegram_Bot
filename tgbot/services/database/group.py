from sqlalchemy import Column, BigInteger, Integer

from tgbot.services.database.base import Base


class Group(Base):
    __tablename__ = 'group'
    group_id = Column(BigInteger, primary_key=True, autoincrement=False)
    group_name = Column(Integer, nullable=False)
