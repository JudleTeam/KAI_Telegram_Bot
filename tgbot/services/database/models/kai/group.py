from sqlalchemy import Column, BigInteger, Integer, select, ForeignKey, Text, String
from sqlalchemy.orm import relationship

from tgbot.services.database.base import Base


class Group(Base):
    __tablename__ = 'group'

    group_id = Column(BigInteger, primary_key=True, autoincrement=False)
    group_leader_id = Column(BigInteger, ForeignKey('kai_user.id'))
    pinned_text = Column(Text, nullable=True)
    group_name = Column(Integer, nullable=False, unique=True)

    syllabus = Column(String(255), nullable=True)
    educational_program = Column(String(255), nullable=True)
    study_schedule = Column(String(255), nullable=True)

    group_leader = relationship('KAIUser', lazy='selectin', foreign_keys=[group_leader_id])

    @classmethod
    async def get_group_by_name(cls, session, group_name):
        if isinstance(group_name, str) and not group_name.isdigit():
            return None

        record = await session.execute(select(Group).where(Group.group_name == int(group_name)))
        return record.scalar()

    @classmethod
    async def get_all(cls, session):
        stmt = select(Group)
        records = await session.execute(stmt)
        return records.scalars().all()
