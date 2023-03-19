from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Speciality(Base):
    __tablename__ = 'speciality'

    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
