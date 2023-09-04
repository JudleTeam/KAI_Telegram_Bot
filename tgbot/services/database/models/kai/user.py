from sqlalchemy import Integer, Column, BigInteger, ForeignKey, String, Date, Boolean
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, Session

from tgbot.services.database.base import Base


class KAIUser(Base):
    __tablename__ = 'kai_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    kai_id = Column(Integer, unique=True, nullable=True)

    telegram_user_id = Column(BigInteger, ForeignKey('telegram_user.telegram_id'), unique=True)

    position = Column(Integer, nullable=True)
    prefix = Column(String(32), nullable=True)
    login = Column(String(64), unique=True, nullable=True)
    password = Column(String(64), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=True, unique=True)
    email = Column(String(64), nullable=False, unique=True)
    sex = Column(String(16), nullable=True)  # Потом вынести типы в отдельную таблицу
    birthday = Column(Date, nullable=True)
    is_leader = Column(Boolean, nullable=False)

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

    speciality = relationship('Speciality', lazy='selectin')
    profile = relationship('Profile', lazy='selectin')
    departament = relationship('Departament', lazy='selectin')
    institute = relationship('Institute', lazy='selectin')

    group = relationship('Group', lazy='selectin', foreign_keys=[group_id])
    telegram_user = relationship('User', lazy='selectin', uselist=False, back_populates='kai_user')

    async def get_classmates(self, db: Session):
        async with db() as session:
            records = await session.execute(select(KAIUser).where(KAIUser.group_id == self.group_id).order_by(KAIUser.position))

        return records.scalars().all()

    @property
    def is_logged_in(self) -> bool:
        return bool(self.kai_id)

    @classmethod
    async def get_by_phone(cls, phone: str, db: Session):
        async with db() as session:
            record = await session.execute(select(KAIUser).where(KAIUser.phone == phone))

        return record.scalar()

    @classmethod
    async def get_by_email(cls, email: str, db: Session):
        async with db() as session:
            record = await session.execute(select(KAIUser).where(KAIUser.email == email))

        return record.scalar()

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int, db: Session):
        async with db() as session:
            record = await session.execute(select(KAIUser).where(KAIUser.telegram_user_id == telegram_id))

        return record.scalar()
