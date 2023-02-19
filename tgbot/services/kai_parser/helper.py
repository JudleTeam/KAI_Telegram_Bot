import datetime

from sqlalchemy import select

from tgbot.services.kai_parser.parser import KaiParser
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


def lesson_type_order(lesson_type: str):
    res = []
    if 'лек' in lesson_type:
        res.append('лек')
    if 'пр' in lesson_type:
        res.append('пр')
    if 'л.р.' in lesson_type:
        res.append('л.р.')
    return ', '.join(res)


schedule_time = (
    (datetime.time(8, 00), datetime.time(9, 30)),
    (datetime.time(9, 40), datetime.time(11, 10)),
    (datetime.time(11, 20), datetime.time(12, 50)),
    (datetime.time(13, 30), datetime.time(15, 0)),
    (datetime.time(15, 10), datetime.time(16, 40)),
    (datetime.time(16, 50), datetime.time(18, 20)),
    (datetime.time(18, 25), datetime.time(19, 55)),
    (datetime.time(20, 0), datetime.time(21, 30))
)


def get_lesson_end_time(start_time: datetime.time, lesson_type: str):
    print(start_time)
    match lesson_type:
        case 'лек' | 'пр':
            for i in schedule_time:
                if i[0] == start_time:
                    return i[1]
        case 'л.р.':
            for k, i in enumerate(schedule_time):
                if i[0] == start_time:
                    return schedule_time[k+1][1]


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
                        end_time=get_lesson_end_time(start_time.time(), lesson['disciplType'])
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


async def get_schedule_by_week_day(group_id: int, day_of_week: int, parity: int, db):
    if day_of_week == 7:
        return None
    async with db.begin() as session:
        stm = select(Schedule).where(Schedule.group_id == group_id, Schedule.number_of_day == day_of_week)
        schedule = (await session.execute(stm)).scalars().all()
        if not schedule:
            await add_group_schedule(group_id, db)
            schedule = (await session.execute(stm)).scalars().all()
            if not schedule:
                return None
        schedule = [i for i in schedule if i.parity_of_week in (0, parity)]
        return schedule

