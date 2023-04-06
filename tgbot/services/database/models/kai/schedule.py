from sqlalchemy import Column, Integer, String, BigInteger, Time

from tgbot.services.database.base import Base


class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(BigInteger, primary_key=True)
    group_id = Column(Integer, nullable=False)
    number_of_day = Column(Integer, nullable=False)
    parity_of_week = Column(String, nullable=True)
    int_parity_of_week = Column(Integer, nullable=True)
    subgroup = Column(Integer, nullable=True)
    lesson_name = Column(String, nullable=False)
    auditory_number = Column(String, nullable=True)
    building_number = Column(String, nullable=True)
    lesson_type = Column(String, nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)
