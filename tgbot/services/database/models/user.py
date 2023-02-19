from sqlalchemy import Column, BigInteger, Integer, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


# Избранные группы
selected_groups = Table(
    'selected_group',
    Base.metadata,
    Column('user_id', ForeignKey('telegram_user.telegram_id'), primary_key=True),
    Column('group_id', ForeignKey('group.group_id'), primary_key=True),
)


class User(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    language_id = Column(Integer, ForeignKey('language.id'), nullable=True)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=True)
    group_id = Column(BigInteger, ForeignKey('group.group_id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=text('NOW()'))
    is_blocked_bot = Column(Boolean, nullable=False, server_default=text('false'))
    is_blocked = Column(Boolean, nullable=False, server_default=text('false'))

    language = relationship('Language', lazy='selectin')
    role = relationship('Role', lazy='selectin')
    group = relationship('Group', lazy='selectin')
    selected_groups = relationship('Group', lazy='selectin', secondary=selected_groups)
