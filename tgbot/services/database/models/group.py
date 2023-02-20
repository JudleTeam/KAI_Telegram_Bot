from sqlalchemy import Column, BigInteger, Integer, select

from tgbot.services.database.base import Base


class Group(Base):
    __tablename__ = 'group'
    group_id = Column(BigInteger, primary_key=True, autoincrement=False)
    group_name = Column(Integer, nullable=False, unique=True)

    @classmethod
    async def get_group_by_name(cls, group_name, db_session):
        async with db_session() as session:
            record = await session.execute(select(Group).where(Group.group_name == int(group_name)))
            return record.scalar()
