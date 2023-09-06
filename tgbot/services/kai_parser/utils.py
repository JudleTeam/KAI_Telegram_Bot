import asyncio
import datetime
from fuzzywuzzy import process, utils

from sqlalchemy.exc import IntegrityError

from tgbot.services.kai_parser.parser import KaiParser
from tgbot.services.database.models import GroupLesson, GroupTeacher, Group
from tgbot.services.kai_parser.schemas import KaiApiError


def get_int_parity(parity_raw: str) -> int:
    templates_odd = ['неч', 'неч.нед.', 'Нечет.нед.', 'неч/-', ]
    templates_even = ['чет', '-/чет', 'четная неделя', 'чет.нед.', ]

    if utils.full_process(parity_raw):
        a = process.extractOne(parity_raw, templates_odd)
        b = process.extractOne(parity_raw, templates_even)

        # parity_of_week 0 - both, 1 - odd, 2 - even
        if a[1] > 70 or b[1] > 70:
            if a[1] > b[1]:
                return 1
            elif b[1] > a[1]:
                return 2
            else:
                return 0

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


def lesson_type_to_text(lesson_type):
    lessons_types = {
        'лек': 'Лекция',
        'пр': 'Практика',
        'л.р.': 'Лабораторная',
        'физ': 'Физра'
    }

    res = [lessons_types[el] for el in lesson_type.split(', ')]
    return res


def get_lesson_end_time(start_time: datetime.time, lesson_type: str):
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

    match lesson_type:
        case 'лек' | 'пр':
            for lesson_time in schedule_time:
                if lesson_time[0] == start_time:
                    return lesson_time[1]
        case 'л.р.':
            for ind, lesson_time in enumerate(schedule_time):
                if lesson_time[0] == start_time:
                    return schedule_time[ind + 1][1]


async def add_group_schedule(group_id: int, async_session):
    response = await KaiParser.get_group_schedule(group_id)

    async with async_session.begin() as session:
        for day in response:
            for lesson in day:
                start_time = datetime.datetime.strptime(lesson.start_time, '%H:%M').time()

                new_lesson = GroupLesson(
                    group_id=group_id,
                    number_of_day=lesson.number_of_day,
                    parity_of_week=lesson.parity_of_week,
                    int_parity_of_week=get_int_parity(lesson.parity_of_week),
                    lesson_name=lesson.lesson_name,
                    auditory_number=lesson.auditory_number,
                    building_number=lesson.building_number,
                    lesson_type=lesson.lesson_type,
                    start_time=start_time,
                    end_time=get_lesson_end_time(start_time, lesson.lesson_type)
                )
                session.add(new_lesson)


async def add_group_teachers(group_id: int, async_session):
    teachers = await KaiParser.get_group_teachers(group_id)
    if not teachers:
        raise KaiApiError

    async with async_session.begin() as session:
        for teacher in teachers:
            teacher.type = lesson_type_order(teacher.type)

            new_teacher = GroupTeacher(
                group_id=group_id,
                teacher_name=teacher.teacher_full_name,
                lesson_type=teacher.type,
                lesson_name=teacher.lesson_name
            )
            session.add(new_teacher)


async def get_schedule_by_week_day(group_id: int, day_of_week: int, parity: int, db):
    async with db.begin() as session:
        schedule = await GroupLesson.get_group_day_schedule(session, group_id, day_of_week)

        if not schedule:  # free day
            return None

        schedule = [schedule_item for schedule_item in schedule if schedule_item.int_parity_of_week in (0, parity)]
        schedule = sorted(schedule, key=lambda x: x.start_time)

        return schedule


async def get_group_teachers(group_id: int, db_session):
    teachers = await GroupTeacher.get_group_teachers(group_id, db_session)
    if teachers:
        return teachers

    try:
        await add_group_teachers(group_id, db_session)
    except KaiApiError:
        return None
    else:
        return await get_group_teachers(group_id, db_session)


async def parse_groups(parsed_groups, db):
    async with db() as session:
        for parsed_group in parsed_groups:
            new_group = Group(
                group_id=parsed_group['id'],
                group_name=int(parsed_group['group'])
            )
            session.add(new_group)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await session.flush()


async def get_group_id(group_name: int) -> int | None:
    groups = await KaiParser.get_group_ids()
    for group in groups:
        if group['group'] == str(group_name):
            return int(group['id'])
    return None


async def main():
    k = KaiParser()
    res = await k.get_group_schedule(23551)  # 23551 - 4120
    for i in res:
        for j in i:
            print(j)
        print('\n')


if __name__ == '__main__':
    asyncio.run(main())
