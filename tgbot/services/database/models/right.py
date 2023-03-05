from sqlalchemy import Column, Integer, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tgbot.misc.texts import rights
from tgbot.services.database.base import Base


class Right(Base):
    __tablename__ = 'right'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), unique=True)

    @classmethod
    async def insert_default_rights(cls, db: Session):
        rights_to_insert = [
            Right(title=rights.edit_homework),
            Right(title=rights.edit_group_events),
            Right(title=rights.send_group_post),
            Right(title=rights.edit_group_pinned_message),
            Right(title='test')
        ]

        async with db() as session:
            for right in rights_to_insert:
                session.add(right)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    await session.flush()

    @classmethod
    async def get_rights_dict(cls, db: Session) -> dict:
        async with db() as session:
            records = await session.execute(select(Right))
            db_rights = records.scalars().all()

        rights_dict = {right.title: right for right in db_rights}

        return rights_dict
