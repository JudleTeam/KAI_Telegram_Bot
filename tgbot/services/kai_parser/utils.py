import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from tgbot.services.kai_parser.parser import KaiParser
from tgbot.services.database.models import Schedule, GroupTeacher, Group
from tgbot.services.kai_parser.schemas import KaiApiError


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


def lesson_type_to_emoji(lesson_type):
    lessons_emoji = {
        'лек': '📢',
        'пр': '📝',
        'л.р.': '🧪',
        'физ': '🏆'
    }

    res = [lessons_emoji[el] for el in lesson_type.split(', ')]
    return res


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
    match lesson_type:
        case 'лек' | 'пр':
            for i in schedule_time:
                if i[0] == start_time:
                    return i[1]
        case 'л.р.':
            for k, i in enumerate(schedule_time):
                if i[0] == start_time:
                    return schedule_time[k + 1][1]


async def add_group_schedule(group_id: int, async_session):
    response = await KaiParser.get_group_schedule(group_id)
    prev_parity = 1
    if not response:
        raise KaiApiError

    for num, day in enumerate(response):
        if not day:
            async with async_session.begin() as session:
                empty_lesson = Schedule(
                    group_id=group_id,
                    number_of_day=num + 1,
                    parity_of_week=prev_parity,
                    lesson_name='',
                    auditory_number='',
                    building_number='',
                    lesson_type='',
                    start_time=datetime.datetime.now().time()
                )
                session.add(empty_lesson)
            continue

        for lesson in day:
            start_time = datetime.datetime.strptime(lesson['dayTime'], '%H:%M')
            if num != 6:
                prev_parity = get_parity(lesson['dayDate'])
            else:
                if lesson['dayDate'] == 'неч':
                    prev_parity = 2
                elif lesson['dayDate'] == 'чет':
                    prev_parity = 1
            async with async_session.begin() as session:
                ex = (await session.execute(select(Schedule).where(
                    Schedule.number_of_day == num + 1,
                    Schedule.parity_of_week == get_parity(lesson['dayDate']),
                    Schedule.lesson_name == lesson['disciplName'],
                    Schedule.auditory_number == lesson['audNum'],
                    Schedule.building_number == lesson['buildNum']
                ))).scalars().all()
                if ex:
                    [await session.delete(el) for el in ex]

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


async def add_group_teachers(group_id: int, async_session):
    response = await KaiParser.get_group_teachers(group_id)
    if not response:
        raise KaiApiError

    async with async_session.begin() as session:
        for teacher in response:
            teacher['type'] = lesson_type_order(teacher['type'])

            new_teacher = GroupTeacher(
                group_id=group_id,
                teacher_name=teacher['teacher_name'],
                lesson_type=teacher['type'],
                lesson_name=teacher['lesson_name']
            )
            session.add(new_teacher)


async def get_schedule_by_week_day(group_id: int, day_of_week: int, parity: int, db):
    if day_of_week == 7:
        return None
    async with db.begin() as session:
        stm = select(Schedule).where(Schedule.group_id == group_id, Schedule.number_of_day == day_of_week)
        schedule = (await session.execute(stm)).scalars().all()
        if not schedule:
            try:
                await add_group_schedule(group_id, db)
            except KaiApiError:
                return None
            schedule = (await session.execute(stm)).scalars().all()
            if not schedule:
                return None
        schedule = [i for i in schedule if i.parity_of_week in (0, parity)]
        return schedule


async def get_group_teachers(group_id: int, db_session):
    teachers = await GroupTeacher.get_group_teachers(group_id, db_session)
    if teachers: return teachers

    try:
        await add_group_teachers(group_id, db_session)
    except KaiApiError:
        return None
    else:
        return await get_group_teachers(group_id, db_session)


async def parse_groups(response, db):
    async with db() as session:
        for i in response:
            new_group = Group(
                group_id=i['id'],
                group_name=int(i['group'])
            )
            session.add(new_group)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await session.flush()


async def get_group_id(group_name: int) -> int | None:
    groups = await KaiParser.get_group_ids()
    for i in groups:
        if i['group'] == str(group_name):
            return int(i['id'])
    return None
