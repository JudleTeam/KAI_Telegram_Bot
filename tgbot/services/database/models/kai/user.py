import os

from environs import Env
from sqlalchemy import Integer, Column, BigInteger, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType

from tgbot.services.database.base import Base


class KAIUser(Base):
    __tablename__ = 'kai_user'

    # Да, это костыль
    env = Env()
    env.read_env(os.getcwd() + r'\.env')
    SECRET_KEY = env.str('SECRET_KEY')

    id = Column(Integer, primary_key=True)

    telegram_user_id = Column(BigInteger, ForeignKey('telegram_user.telegram_id'), unique=True)

    login = Column(String(64), unique=True, nullable=True)
    password = Column(StringEncryptedType(key=SECRET_KEY), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=True, unique=True)
    email = Column(String(64), nullable=True)

    group_id = Column(BigInteger, ForeignKey('group.group_id', name='fk_kai_user_group'), nullable=False)
    zach_number = Column(Integer, nullable=True)  # Уникальный?
    competition_type = Column(String(64), nullable=True)  # Потом вынести типы в отдельную таблицу
    contract_number = Column(BigInteger, nullable=True)  # Уникальный?
    edu_level = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    edu_cycle = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    edu_qualification = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    program_form = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу
    status = Column(String(64), nullable=True)  # Потом вынести в отдельную таблицу

    speciality_id = Column(Integer, ForeignKey('speciality.id'), nullable=True)
    profile_id = Column(Integer, ForeignKey('profile.id'), nullable=True)
    institute_id = Column(Integer, ForeignKey('institute.id'), nullable=True)
    departament_id = Column(Integer, ForeignKey('departament.id'), nullable=True)

    specialty = relationship('Speciality', lazy='selectin')
    profile = relationship('Profile', lazy='selectin')
    departament = relationship('Departament', lazy='selectin')
    institute = relationship('Institute', lazy='selectin')
