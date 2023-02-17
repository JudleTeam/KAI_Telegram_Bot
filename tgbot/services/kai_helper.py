import asyncio
import datetime
from kai_parser import KaiParser
from tgbot.services.database import Schedule


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


async def add_group_schedule(group_name: int, async_session):
    k = KaiParser()
    group_id = await k.get_group_id(group_name)
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


async def main():
    await add_group_schedule(6110, '1111')


if __name__ == '__main__':
    asyncio.run(main())
