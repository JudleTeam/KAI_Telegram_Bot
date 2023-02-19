from sqlalchemy import Column, BigInteger, String, ForeignKey

from tgbot.services.database.base import Base


class GroupTeacher(Base):
    __tablename__ = 'group_teacher'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey('group.group_id'))
    teacher_name = Column(String, nullable=False)
    lesson_type = Column(String, nullable=True)
    lesson_name = Column(String, nullable=False)
