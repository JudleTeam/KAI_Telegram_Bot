from sqlalchemy import Column, BigInteger, String, ForeignKey, select
from sqlalchemy.orm import relationship

from tgbot.services.database.base import Base


class GroupTeacher(Base):
    __tablename__ = 'group_teacher'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey('group.group_id'))
    teacher_name = Column(String, nullable=False)
    lesson_type = Column(String, nullable=True)
    lesson_name = Column(String, nullable=False)

    group = relationship('Group', lazy='selectin', uselist=False)

    @classmethod
    async def get_group_teachers(cls, group_id, db_session):
        async with db_session() as session:
            records = await session.execute(select(GroupTeacher).where(GroupTeacher.group_id == group_id))
            return records.scalars().all()
