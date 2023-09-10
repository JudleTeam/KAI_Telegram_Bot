from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Speciality(Base):
    __tablename__ = 'speciality'

    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    @classmethod
    async def get_or_create(cls, session, spec_id: int, name: str, code: str):
        spec = await session.get(Speciality, spec_id)
        if not spec:
            spec = Speciality(id=spec_id, name=name, code=code)
            session.add(spec)

        return spec
