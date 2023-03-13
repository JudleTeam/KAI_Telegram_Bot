from sqlalchemy import Column, BigInteger, Integer, ForeignKey, DateTime, Boolean, Table, select
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


# Избранные группы
selected_groups = Table(
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


class User(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    language_id = Column(Integer, ForeignKey('language.id'), nullable=True)
    group_id = Column(BigInteger, ForeignKey('group.group_id', name='fk_user_group'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=text('NOW()'))
    is_blocked_bot = Column(Boolean, nullable=False, server_default=text('false'))
    is_blocked = Column(Boolean, nullable=False, server_default=text('false'))

    language = relationship('Language', lazy='selectin')
    group = relationship('Group', lazy='selectin', foreign_keys=[group_id])
    selected_groups = relationship('Group', lazy='selectin', secondary=selected_groups)
    roles = relationship('Role', lazy='selectin', secondary=user_roles)

    def has_right_to(self, right: str):
        for role in self.roles:
            if right in role.get_all_rights():
                return True

        return False

    @classmethod
    async def get_all(cls, db: Session) -> list:
        async with db() as session:
            records = await session.execute(select(User))
            users = records.scalars().all()

        return users
