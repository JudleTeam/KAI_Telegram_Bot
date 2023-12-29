import datetime

from aiogram import Dispatcher, Bot
from sqlalchemy import select, text, or_
from sqlalchemy.orm import selectinload, joinedload

from tgbot.services.database.models import GroupLesson, Teacher, Discipline, Departament, Homework, User, KAIUser


async def get_group_teachers(session, group_id: int, offset: int = 0, limit: int = 100):
    stmt = (
        select(Teacher)
        .join(GroupLesson.teacher)
        .where(GroupLesson.group_id == group_id)
        .limit(limit)
        .offset(offset)
        .order_by(Teacher.name)
        .distinct()
    )

    records = await session.execute(stmt)

    return records.scalars().all()


async def get_group_teachers_dict(session, group_id: int):
    """
    Возвращает всех преподавателей для группы, кроме преподавателей кафедры

    (Возможно потом сделать вывод преподавателей кафедры, вместе с названием кафедры)
    """
    stmt = (
        select(Teacher.name, GroupLesson.lesson_type, Discipline.name, Departament.name)
        .join(GroupLesson.teacher)
        .join(Teacher.departament)
        .join(GroupLesson.discipline)
        .where(GroupLesson.group_id == group_id)
        .order_by(text('discipline.name'))
    )

    records = await session.execute(stmt)

    teachers = dict()
    for record in records:
        teacher_name, lesson_type, lesson_name, departament = record
        if teacher_name in teachers and lesson_type not in teachers[teacher_name]['lesson_types']:
            teachers[teacher_name]['lesson_types'].append(lesson_type)
            teachers[teacher_name]['lesson_types'].sort()
        else:
            teachers[teacher_name] = {
                'lesson_name': lesson_name,
                'departament': departament,
                'lesson_types': [lesson_type]
            }

    return teachers


async def get_lessons_with_homework(session, group_id: int, date: datetime.date):
    week_num = int(date.strftime('%V'))
    int_parity = 2 if not week_num % 2 else 1

    stmt = (
        select(GroupLesson)
        .options(joinedload(GroupLesson.homework.and_(Homework.date == date)))
        .where(
            GroupLesson.group_id == group_id,
            GroupLesson.number_of_day == date.isoweekday(),
            or_(
                GroupLesson.int_parity_of_week == int_parity,
                GroupLesson.int_parity_of_week == 0
            )
        )
        .order_by(GroupLesson.start_time)
    )

    records = await session.execute(stmt)
    return records.unique().scalars().all()


async def get_telegram_ids_by_group(session, group_id: int, without_id: int | None = None, for_notification: bool = None):
    stmt = (
        select(KAIUser.telegram_user_id)
        .join(User)
        .where(
            KAIUser.group_id == group_id,
            KAIUser.telegram_user_id != without_id,
            KAIUser.telegram_user_id != None
        )
    )

    if for_notification is not None:
        stmt = stmt.where(User.send_homework_notifications == for_notification)

    records = await session.execute(stmt)

    return records.scalars().all()
