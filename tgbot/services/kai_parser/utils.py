import asyncio
import datetime
import logging
from pprint import pprint

from sqlalchemy.exc import IntegrityError

from tgbot.services.kai_parser.parser import KaiParser
from tgbot.services.database.models import GroupLesson, Group, Departament, Teacher, Discipline
from tgbot.services.kai_parser.schemas import KaiApiError, GroupsResult


def parse_parity(parity: str) -> int:
    """
    0 - any week
    1 - odd week
    2 - even week
    """

    odd = False
    even = False

    # 'нея' - typo. Check misc/possible_parity.txt
    if 'нечет' in parity or 'неч' in parity or 'нея' in parity:
        odd = True
        parity = parity.replace('нечет', '')

    if 'чет' in parity:
        even = True

    if odd and not even:
        return 1
    if even and not odd:
        return 2

    return 0


def lesson_type_to_emoji(lesson_type: str):
    lessons_emoji = {
        'лек': '📢',
        'пр': '📝',
        'л.р.': '🧪',
        'физ': '🏆',
        'конс': '❓'
    }

    return lessons_emoji[lesson_type]


def lesson_type_to_text(lesson_type: str):
    lessons_text = {
        'лек': 'Лекция',
        'пр': 'Практика',
        'л.р.': 'Лабораторная',
        'физ': 'Физра',
        'конс': 'Консультация'
    }

    return lessons_text[lesson_type]


def get_lesson_end_time(start_time: datetime.time, lesson_type: str) -> datetime.time | None:
    """
    Время пар не подходит для филиалов. На момент 2023-2024 учебного года на сайте КАИ есть расписание только некоторых
    филиалов, например группы с номером из 5 цифр или начинающиеся с "8" относятся к каким-то филиалам

    (Возможно стоит сделать адаптивное определение времени - получить всё возможное время начала пары для группы или
    факультета и на его основе определять время конца пары, т.е. просто собирать отдельно список start_times.
    А возможно и не стоит думать о других филиалах вообще)
    """
    start_times = (
        datetime.timedelta(hours=8, minutes=00),
        datetime.timedelta(hours=9, minutes=40),
        datetime.timedelta(hours=11, minutes=20),
        datetime.timedelta(hours=13, minutes=30),
        datetime.timedelta(hours=15, minutes=10),
        datetime.timedelta(hours=16, minutes=50),
        datetime.timedelta(hours=18, minutes=25),
        datetime.timedelta(hours=20, minutes=00)
    )

    start_time = datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)

    if start_time not in start_times:
        return None

    lesson_timedelta = datetime.timedelta(hours=1, minutes=30)

    """ В этом семестре лабы разделены на 2 пары, по полтора часа """
    # if lesson_type == 'л.р.':
    #     next_lesson_ind = start_times.index(start_time) + 1
    #     if next_lesson_ind > len(start_times) - 1:
    #         # Бывают лабораторные работы в 20:00, видимо они длятся одну пару
    #         next_lesson_ind = len(start_times) - 1
    #     end_time = start_times[next_lesson_ind] + lesson_timedelta
    # else:
    #     end_time = start_time + lesson_timedelta

    end_time = start_time + lesson_timedelta

    return (datetime.datetime.min + end_time).time()


async def get_schedule_by_week_day(group_id: int, day_of_week: int, parity: int, db):
    async with db.begin() as session:
        schedule = await GroupLesson.get_group_day_schedule(session, group_id, day_of_week)

        if not schedule:  # free day
            return None

        schedule = [schedule_item for schedule_item in schedule if schedule_item.int_parity_of_week in (0, parity)]
        schedule = sorted(schedule, key=lambda x: x.start_time)

        return schedule


async def parse_groups(parsed_groups: list[GroupsResult], db):
    async with db() as session:
        for parsed_group in parsed_groups:
            new_group = Group(
                group_id=parsed_group.id,
                group_name=int(parsed_group.group)
            )
            session.add(new_group)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                await session.flush()


async def parse_all_groups_schedule(db):
    """
    Обновляет расписание для всех групп из базы. Занимает 5-10 минут
    """
    logging.info('Start parsing all groups')
    async with db.begin() as session:
        groups = await Group.get_all(session)
        total = len(groups)
        for parsed, group in enumerate(groups, start=1):
            try:
                group_schedule = await KaiParser.get_group_schedule(group.group_id)
                new_schedule = list()
                for lesson in group_schedule:
                    departament = await Departament.get_or_create(session, lesson.orgUnitId, lesson.orgUnitName)
                    teacher = await Teacher.get_or_create(session, lesson.prepodLogin, lesson.prepodName, departament)
                    discipline = await Discipline.get_or_create(session, lesson.disciplNum, lesson.disciplName)
                    new_lesson = await GroupLesson.update_or_create(
                        session, group.group_id, lesson, discipline, teacher, parse_parity(lesson.dayDate),
                        get_lesson_end_time(lesson.dayTime, lesson.disciplType)
                    )
                    new_schedule.append(new_lesson)

                deleted_lessons = await GroupLesson.clear_old_schedule(session, group.group_id, new_schedule)
                # Удаленные пары для отслеживания изменений в расписании

            except Exception as error:
                logging.error(f'Error with group {group.group_name}: {error}')
                continue

            if parsed % 50 == 0:
                logging.info(f'{parsed}/{total} parsed')

    logging.info('All groups parsing complete')


async def main():
    k = KaiParser()
    groups = await k.get_group_ids()
    possible_parity = set()
    total = len(groups)
    for num, group in enumerate(groups[:2], start=1):
        schedule = await k.get_group_schedule(group.id)  # 23551 - 4120

        pprint(schedule)
        print(f'{num}/{total}')
        # pprint(schedule)
        # print()

    pprint(possible_parity)


if __name__ == '__main__':
    asyncio.run(main())
