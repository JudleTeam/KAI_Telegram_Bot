import asyncio
import datetime
from fuzzywuzzy import process

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from tgbot.services.kai_parser.parser import KaiParser
from tgbot.services.database.models import Schedule, GroupTeacher, Group
from tgbot.services.kai_parser.schemas import KaiApiError


def get_int_parity(parity_raw: str) -> int:
    templates_odd = ['неч', 'неч.нед.', 'Нечет.нед.', 'неч/-', ]
    templates_even = ['чет', '-/чет', 'четная неделя', 'чет.нед.', ]

    a = process.extractOne(parity_raw, templates_odd)
    b = process.extractOne(parity_raw, templates_even)
    # parity_of_week 0 - both, 1 - odd, 2 - even
    if a[1] > 70 or b[1] > 70:
        if a[1] > b[1]:
            parity_of_week = 1
        elif b[1] > a[1]:
            parity_of_week = 2
        else:
            parity_of_week = 0
    else:  # dates or nothing
        if ',' in parity_raw:
            sep = ','
        else:
            sep = ' '
        if '/' in parity_raw:
            parity_raw = parity_raw.replace('/', sep)
        h = parity_raw.split(sep)

        year = datetime.datetime.now().year
        sum_k = []
        for j in h:
            try:
                try:
                    date = datetime.datetime.strptime(j, '%d.%m.%Y')
                except:
                    j = j.strip() + f'.{year}'
                date = datetime.datetime.strptime(j, '%d.%m.%Y')

                sum_k.append(int(date.strftime("%V")) % 2)  # append 0 or 1
            except:
                pass
        else:
            if sum_k and len(sum_k) * sum_k[0] == sum(sum_k):
                parity_of_week = sum_k[0]
            else:
                parity_of_week = 0
    return parity_of_week


def get_subgroups(parity_raw: str):
    """Return number of subgroup and string for parity of week if had one else return 0"""
    index_1 = parity_raw.find('подгруппа')
    index_2 = parity_raw.find('п/г')
    if index_1 != -1:
        a = parity_raw[index_1 - 2: index_1 - 1]
        b = parity_raw[index_1 - 5: index_1 - 4]
        if a.isdigit():
            # parity_raw = parity_raw.replace(parity_raw[index_1 - 2: index_1 + 9], '')
            return int(a)
        elif b.isdigit():
            # parity_raw = parity_raw.replace(parity_raw[index_1 - 5: index_1 + 9], '')
            return int(b)
    elif index_2 != -1:
        a = parity_raw[index_2 - 1: index_2]
        if a.isdigit():
            # parity_raw = parity_raw.replace(parity_raw[index_2 - 1: index_2 + 3], '')
            return int(a)
    elif '/' in parity_raw:
        a, b = parity_raw.split('/')  # 20.03, 25.03 / 05.04, 15.04 чет
        if ',' in a:
            sep = ','
        else:
            sep = ' '
        year = datetime.datetime.now().year

        res_dates = []
        for i in (a, b):
            dates = []
            for j in i.split(sep):
                try:
                    try:
                        date = datetime.datetime.strptime(j, '%d.%m.%Y')
                    except:
                        j = j.strip() + f'.{year}'
                    date = datetime.datetime.strptime(j, '%d.%m.%Y')
                    dates.append(str(date.date()))
                except:
                    pass
            else:
                res_dates.append(dates)
        return (1, res_dates[0]), (2, res_dates[1])
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
    for i in response:
        for j in i:
            print(j)
        print('\n')

    for day in response:
        for lesson in day:
            start_time = datetime.datetime.strptime(lesson.start_time, '%H:%M').time()

            async with async_session.begin() as session:
                new_lesson = Schedule(
                    group_id=group_id,
                    number_of_day=lesson.number_of_day,
                    parity_of_week=lesson.parity_of_week,
                    int_parity_of_week=get_int_parity(lesson.parity_of_week),
                    subgroup=get_subgroups(lesson.parity_of_week),
                    lesson_name=lesson.lesson_name,
                    auditory_number=lesson.auditory_number,
                    building_number=lesson.building_number,
                    lesson_type=lesson.lesson_type,
                    start_time=start_time,
                    end_time=get_lesson_end_time(start_time, lesson.lesson_type)
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


async def get_schedule_by_week_day(group_id: int, subgroup: int, day_of_week: int, parity: int, db):
    async with db.begin() as session:
        stm = select(Schedule).where(
            Schedule.group_id == group_id,
            Schedule.number_of_day == day_of_week,
            Schedule.subgroup == subgroup
        )
        schedule = (await session.execute(stm)).scalars().all()
        if not schedule:  # free day
            return None

        schedule = [i for i in schedule if i.int_parity_of_week in (0, parity)]
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


async def main():
    k = KaiParser()
    res = await k.get_group_schedule(23551)  # 23551 - 4120
    for i in res:
        for j in i:
            print(j)
            print(get_subgroups(j.parity_of_week))
        print('\n')


if __name__ == '__main__':
    asyncio.run(main())
