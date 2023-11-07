from sqlalchemy import Column, String, Integer, ForeignKey, text, select, func, or_
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

    @classmethod
    async def search_by_name(cls, session, name, similarity=0.3, limit=50, offset=0):
        await session.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))
        name = name.lower()
        records = await session.execute(
            select(Teacher).where(
                or_(func.similarity(Teacher.name, name) > similarity, Teacher.name.ilike(f'%{name}%'))
            ).limit(limit).offset(offset)
        )
        return records.scalars().all()

    @property
    def short_name(self):
        name_parts = self.name.split()
        letters = [f'{part[0]}.' for part in name_parts[1:]]
        short_name = f'{name_parts[0]} {"".join(letters)}'

        return short_name

    def __repr__(self):
        return f'{self.name} | {self.login}'
