from sqlalchemy import Column, String, Integer

from tgbot.services.database.base import Base


class Departament(Base):
    __tablename__ = 'departament'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    @classmethod
    async def get_or_create(cls, session, dep_id: int, name: str):
        dep = await session.get(Departament, dep_id)
        if not dep:
            dep = Departament(id=dep_id, name=name)
            session.add(dep)

        return dep

    @property
    def short_name(self):
        name_parts = self.name.title().split()
        short_name = ''
        for ind, part in enumerate(name_parts):
            if part.lower() == 'кафедра':
                continue

            if part.lower() == 'и':
                if not (len(name_parts) - 1 > ind > 0 and name_parts[ind + 1].lower()[0] != 'и' and name_parts[ind - 1].lower()[0] != 'и'):
                    continue

                short_name += 'и'
                continue

            if part.lower() == 'как':
                if not (len(name_parts) - 1 > ind > 0 and name_parts[ind + 1].lower()[0] != 'к' and name_parts[ind - 1].lower()[0] != 'к'):
                    continue

                short_name += 'к'
                continue

            short_name += part[0]

        return short_name
