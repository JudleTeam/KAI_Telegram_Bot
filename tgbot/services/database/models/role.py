from sqlalchemy import Column, Integer, String, Table, ForeignKey, select, Boolean
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, Session

from tgbot.misc.texts import roles, rights
from tgbot.services.database.base import Base
from tgbot.services.database.models.right import Right

# Права роли
role_rights = Table(
    'role_right',
    Base.metadata,
    Column('role_id', ForeignKey('role.id'), primary_key=True),
    Column('right_id', ForeignKey('right.id'), primary_key=True),
)


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(40), unique=True, nullable=False)
    to_show = Column(Boolean, nullable=False)

    rights = relationship('Right', lazy='selectin', secondary=role_rights)

    def get_all_rights(self) -> list[str]:
        return [right.title for right in self.rights]

    @classmethod
    async def get_roles_dict(cls, db: Session):
        async with db() as session:
            records = await session.execute(select(Role))
            db_roles = records.scalars().all()

        return {role.title: role for role in db_roles}

    @classmethod
    async def get_by_title(cls, role: str, db: Session):
        async with db() as session:
            record = await session.execute(select(Role).where(Role.title == role))
            role = record.scalar()

        return role

    @classmethod
    async def insert_default_roles(cls, db: Session):
        rights_dict = await Right.get_rights_dict(db)
        roles_to_insert = [
            Role(title=roles.student, to_show=True, rights=[

            ]),
            Role(title=roles.group_leader, to_show=True, rights=[
                rights_dict[rights.edit_homework],
                rights_dict[rights.edit_group_events],
                rights_dict[rights.edit_group_pinned_message]
            ]),
            Role(title=roles.authorized, to_show=False, rights=[

            ])
        ]

        async with db() as session:
            for role in roles_to_insert:
                session.add(role)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    await session.flush()
