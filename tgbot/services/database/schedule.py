from sqlalchemy import Column, Integer, String, DateTime

from tgbot.services.database.base import Base


class Schedule(Base):
    __tablename__ = 'schedule'
    group_id = Column(Integer, nullable=False)
    number_of_day = Column(Integer, nullable=False)
    parity_of_week = Column(Integer, nullable=True)
    lesson_name = Column(String, nullable=False)
    auditory_number = Column(String, nullable=True)
    building_number = Column(Integer, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
