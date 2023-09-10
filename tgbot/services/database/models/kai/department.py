from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Departament(Base):
    __tablename__ = 'departament'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    @classmethod
    async def get_or_create(cls, session, dep_id: int, name: str):
        dep = await session.get(Departament, dep_id)
        if not dep:
            dep = Departament(id=dep_id, name=name)
            session.add(dep)

        return dep
