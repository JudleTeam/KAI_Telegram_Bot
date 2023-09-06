from sqlalchemy import Column, Integer, String, BigInteger, Time, select, delete

from tgbot.services.database.base import Base


class GroupLesson(Base):
    __tablename__ = 'group_lesson'
    id = Column(BigInteger, primary_key=True)
    group_id = Column(Integer, nullable=False)
    number_of_day = Column(Integer, nullable=False)
    parity_of_week = Column(String, nullable=True)
    int_parity_of_week = Column(Integer, nullable=True)
    lesson_name = Column(String, nullable=False)
    auditory_number = Column(String, nullable=True)
    building_number = Column(String, nullable=True)
    lesson_type = Column(String, nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)

    @classmethod
    async def get_group_day_schedule(cls, session, group_id, day):
        stmt = select(GroupLesson).where(
            GroupLesson.group_id == group_id,
            GroupLesson.number_of_day == day
        )

        records = await session.execute(stmt)
        return records.scalars().all()

    @classmethod
    async def clear_group_schedule(cls, session, group_id):
        stmt = delete(GroupLesson).where(GroupLesson.group_id == group_id)
        await session.execute(stmt)
