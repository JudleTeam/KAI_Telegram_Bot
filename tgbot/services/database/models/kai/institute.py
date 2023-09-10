from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Institute(Base):
    __tablename__ = 'institute'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    @classmethod
    async def get_or_create(cls, session, inst_id: int, name: str):
        inst = await session.get(Institute, inst_id)
        if not inst:
            inst = Institute(id=inst_id, name=name)
            session.add(inst)

        return inst
