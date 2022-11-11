from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class User(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    language_id = Column(Integer, ForeignKey('language.id'))
    role_id = Column(Integer, ForeignKey('role.id'))
    created_at = Column(DateTime(), server_default=text('NOW()'))

    language = relationship('Language', backref='user')
    role = relationship('Role', backref='user')


class Language(Base):
    __tablename__ = 'language'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(20), nullable=False)
    code = Column(String(2), unique=True, nullable=False)


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    title = Column(String(40), nullable=False)
