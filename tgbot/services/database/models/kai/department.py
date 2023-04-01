from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Departament(Base):
    __tablename__ = 'departament'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
