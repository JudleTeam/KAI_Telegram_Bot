from sqlalchemy import Column, BigInteger, String

from tgbot.services.database.base import Base


class GroupTeacher(Base):
    __tablename__ = 'group_teacher'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    teacher_name = Column(String, nullable=False)
    lesson_type = Column(String, nullable=True)
