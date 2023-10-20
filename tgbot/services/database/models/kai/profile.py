from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Profile(Base):
    __tablename__ = 'profile'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    @classmethod
    async def get_or_create(cls, session, prof_id: int, name: str):
        prof = await session.get(Profile, prof_id)
        if not prof:
            prof = Profile(id=prof_id, name=name)
            session.add(prof)

        return prof
