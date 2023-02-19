import asyncio
import datetime
from tgbot.services.kai_parser import KaiParser
from tgbot.services.database.models import Schedule, GroupTeacher


class KaiApiError(Exception):
    """Can't get data from Kai site"""


def get_parity(week: str):
    match week:
        case 'неч':
            return 1
        case 'чет':
            return 2
        case _:
            return 0


def get_duration(lesson_type: str):
    match lesson_type:
        case 'лек' | 'пр':
            return datetime.timedelta(hours=1, minutes=30)
        case 'л.р.':
            return datetime.timedelta(hours=3)


def lesson_type_order(lesson_type: str):
    res = []
    if 'лек' in lesson_type:
        res.append('лек')
    if 'пр' in lesson_type:
        res.append('пр')
    if 'л.р.' in lesson_type:
        res.append('л.р.')
    return ', '.join(res)


async def add_group_schedule(group_id: int, async_session):
    k = KaiParser()
    response = await k.get_group_schedule(group_id)
    if response:
        for num, day in enumerate(response):
            for lesson in day:
                print(lesson)
                start_time = datetime.datetime.strptime(lesson['dayTime'], '%H:%M')
                async with async_session.begin() as session:
                    new_lesson = Schedule(
                        group_id=group_id,
                        number_of_day=num + 1,
                        parity_of_week=get_parity(lesson['dayDate']),
                        lesson_name=lesson['disciplName'],
                        auditory_number=lesson['audNum'],
                        building_number=lesson['buildNum'],
                        lesson_type=lesson['disciplType'],
                        start_time=start_time.time(),
                        end_time=(start_time + get_duration(lesson['disciplType'])).time()
                    )
                    session.add(new_lesson)
    else:
        raise KaiApiError


async def add_group_teachers(group_id: int, async_session):
    k = KaiParser()
    response = await k.get_group_teachers(group_id)
    if response:
        for teacher in response:
            async with async_session.begin() as session:
                teacher['type'] = lesson_type_order(teacher['type'])

                new_teacher = GroupTeacher(
                    group_id=group_id,
                    teacher_name=teacher['teacher_name'],
                    lesson_type=teacher['type'],
                    lesson_name=teacher['lesson_name']
                )
                session.add(new_teacher)
    else:
        raise KaiApiError
