from sqlalchemy import Column, BigInteger, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class User(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    language_id = Column(Integer, ForeignKey('language.id'), nullable=True)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=text('NOW()'))
    is_blocked_bot = Column(Boolean, nullable=False, server_default=text('false'))
    is_blocked = Column(Boolean, nullable=False, server_default=text('false'))
    group_id = Column(BigInteger, ForeignKey('group.group_id'), nullable=True)

    language = relationship('Language', lazy='selectin', backref='user')
    role = relationship('Role', lazy='selectin', backref='user')
    group = relationship('Group', lazy='selectin', backref='user')
