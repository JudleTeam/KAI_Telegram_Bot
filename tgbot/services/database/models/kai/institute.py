from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Institute(Base):
    __tablename__ = 'institute'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
