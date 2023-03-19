from sqlalchemy import Column, BigInteger, Integer, select, ForeignKey
from sqlalchemy.orm import relationship

from tgbot.services.database.base import Base


class Group(Base):
    __tablename__ = 'group'

    group_id = Column(BigInteger, primary_key=True, autoincrement=False)
    group_leader_id = Column(BigInteger, ForeignKey('telegram_user.telegram_id'))
    group_name = Column(Integer, nullable=False, unique=True)

    group_leader = relationship('User', lazy='selectin', foreign_keys=[group_leader_id])

    @classmethod
    async def get_group_by_name(cls, group_name, db_session):
        if isinstance(group_name, str) and not group_name.isdigit():
            return None

        async with db_session() as session:
            record = await session.execute(select(Group).where(Group.group_name == int(group_name)))
            return record.scalar()
