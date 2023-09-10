from sqlalchemy import Column, BigInteger, Integer, ForeignKey, DateTime, Boolean, Table, select, String
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


# Избранные группы
favorite_group = Table(
    'selected_group',
    Base.metadata,
    Column('user_id', ForeignKey('telegram_user.telegram_id'), primary_key=True),
    Column('group_id', ForeignKey('group.group_id'), primary_key=True),
)

# Роли пользователя
user_roles = Table(
    'user_role',
    Base.metadata,
    Column('user_id', ForeignKey('telegram_user.telegram_id'), primary_key=True),
    Column('role_id', ForeignKey('role.id'), primary_key=True)
)


# class FavoriteGroup(Base):
#     __tablename__ = 'favorite_group'
#
#     user_id = Column(ForeignKey('telegram_user.telegram_id'), primary_key=True)
#     group_id = Column(ForeignKey('group.group_id'), primary_key=True)
#
#     @classmethod
#     async def get_all(cls, session):
#         stmt = select(FavoriteGroup)
#         records = await session.execute(stmt)
#         return records.scalars().all()


class User(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    language_id = Column(Integer, ForeignKey('language.id'), nullable=True)
    group_id = Column(BigInteger, ForeignKey('group.group_id', name='fk_user_group'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=text('NOW()'))
    is_blocked_bot = Column(Boolean, nullable=False, server_default=text('false'))
    is_blocked = Column(Boolean, nullable=False, server_default=text('false'))
    phone = Column(String(32), nullable=True, unique=True)

    language = relationship('Language', lazy='selectin')
    group = relationship('Group', lazy='selectin', foreign_keys=[group_id])
    favorite_groups = relationship('Group', lazy='selectin', secondary=favorite_group)
    roles = relationship('Role', lazy='selectin', secondary=user_roles)
    kai_user = relationship('KAIUser', lazy='selectin', uselist=False, back_populates='telegram_user')

    def has_role(self, role_title: str):
        return role_title in [role.title for role in self.roles]

    def remove_role(self, role_title: str):
        for role in self.roles:
            if role.title == role_title:
                self.roles.remove(role)
                break

    def has_right_to(self, right: str):
        for role in self.roles:
            if right in role.get_all_rights():
                return True

        return False

    def get_roles_titles(self, to_show=True):
        if to_show:
            return [role.title for role in self.roles if role.to_show]

        return [role.title for role in self.roles]

    @classmethod
    async def get_by_phone(cls, session, phone):
        record = await session.execute(select(User).where(User.phone == phone))

        return record.scalar()

    @classmethod
    async def get_all(cls, db: Session) -> list:
        async with db() as session:
            records = await session.execute(select(User))
            users = records.scalars().all()

        return users

    @classmethod
    async def get_all_selected_groups(cls, session):
        stmt = select(User.group_id)
        records = await session.execute(stmt)
        return records.scalars().all()
