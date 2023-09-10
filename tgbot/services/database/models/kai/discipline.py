from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from tgbot.services.database.base import Base


class Discipline(Base):
    __tablename__ = 'discipline'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    @classmethod
    async def get_or_create(cls, session, dis_id: int, name: str):
        discipline = await session.get(Discipline, dis_id)
        if not discipline:
            discipline = Discipline(id=dis_id, name=name)
            session.add(discipline)

        return discipline
