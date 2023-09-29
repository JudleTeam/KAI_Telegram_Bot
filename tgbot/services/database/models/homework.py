import datetime
from typing import Sequence

from iso_language_codes import language_dictionary
from sqlalchemy import Column, Integer, Boolean, String, text, Text, Date, ForeignKey, BigInteger
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

from tgbot.services.database.base import Base


class Homework(Base):
    __tablename__ = 'homework'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    lesson_id = Column(ForeignKey('group_lesson.id'), nullable=False)

    lesson = relationship('GroupLesson', lazy='selectin', backref='homework')

    @classmethod
    async def get_by_lesson_and_date(cls, session, lesson_id, date):
        record = await session.execute(
            select(Homework).where(Homework.lesson_id == lesson_id, Homework.date == date)
        )

        return record.scalar()
