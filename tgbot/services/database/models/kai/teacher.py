from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from tgbot.services.database.base import Base


class Teacher(Base):
    __tablename__ = 'teacher'

    login = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    departament_id = Column(Integer, ForeignKey('departament.id'))

    departament = relationship('Departament', lazy='selectin', backref='teachers')

    @classmethod
    async def get_or_create(cls, session, login: str, name: str, departament):
        if not login:
            return None

        teacher = await session.get(Teacher, login)
        if not teacher:
            teacher = Teacher(login=login, name=name, departament=departament)
            session.add(teacher)

        return teacher

    @property
    def short_name(self):
        name_parts = self.name.split()
        letters = [f'{part[0]}.' for part in name_parts[1:]]
        short_name = f'{name_parts[0]} {"".join(letters)}'

        return short_name
