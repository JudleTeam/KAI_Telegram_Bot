from pprint import pprint

from sqlalchemy import select, text

from tgbot.services.database.models import GroupLesson, Teacher, Discipline, Departament


async def get_group_teachers(session, group_id: int):
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
