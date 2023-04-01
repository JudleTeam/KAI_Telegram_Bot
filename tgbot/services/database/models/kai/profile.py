from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Profile(Base):
    __tablename__ = 'profile'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
