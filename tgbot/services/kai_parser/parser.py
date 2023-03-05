import asyncio
from dataclasses import dataclass

import aiohttp
from sqlalchemy.exc import IntegrityError

from tgbot.services.database.models import Group


@dataclass
class Teacher:
    type: str
    lesson_name: str
    teacher_full_name: str


class KaiParser:
    base_url = 'https://kai.ru/raspisanie'

    @classmethod
    async def _get_schedule_data(cls, group_id: int) -> list:
        async with aiohttp.ClientSession() as session:
            async with await session.post(cls.base_url, data="groupId=" + str(group_id),
                                          headers={'Content-Type': "application/x-www-form-urlencoded",
                                                   "user-agent": "KAI_PUP"},
                                          params={"p_p_id": "pubStudentSchedule_WAR_publicStudentSchedule10",
                                                  "p_p_lifecycle": "2", "p_p_resource_id": "schedule"},
                                          timeout=3) as response:
                response = await response.json(content_type='text/html')
                return response

    @classmethod
    async def get_group_ids(cls) -> list:
        async with aiohttp.ClientSession() as session:
            async with await session.post(
                    cls.base_url + "?p_p_id=pubStudentSchedule_WAR_publicStudentSchedule10&p_p_lifecycle=2"
                                   "&p_p_resource_id=getGroupsURL&query=",
                    headers={'Content-Type': "application/x-www-form-urlencoded", "user-agent": "KAI_PUP"},
                    params={"p_p_id": "pubStudentSchedule_WAR_publicStudentSchedule10", "p_p_lifecycle": "2",
                            "p_p_resource_id": "schedule"}, timeout=8) as response:
                response = await response.json(content_type='text/html')
                return response

    @classmethod
    async def parse_groups(cls, response, db):
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

    @classmethod
    async def get_group_id(cls, group_name: int) -> int | None:
        groups = await cls.get_group_ids()
        for i in groups:
            if i['group'] == str(group_name):
                return int(i['id'])
        return None

    @classmethod
    def _parse_teachers(cls, response) -> list:
        # виды занятий, название дисциплины, фио
        res = []
        for key in response:  # дни недели от 1 до 6
            for el in response[key]:
                lesson_type = el['disciplType'].strip()
                lesson_name = el['disciplName'].strip()
                teacher_name = el['prepodName'].strip()
                if not teacher_name:
                    teacher_name = 'Не задан'
                for i in res:
                    if i['lesson_name'] == lesson_name and i['teacher_name'] == teacher_name.title():
                        if lesson_type not in i['type']:
                            i['type'] += f', {lesson_type}'
                        break
                else:
                    res.append(
                        {'type': lesson_type,
                         'lesson_name': lesson_name,
                         'teacher_name': teacher_name.title()}
                    )
        return res

    @classmethod
    def _parse_schedule(cls, response) -> list:
        res = [0] * 6
        for key in sorted(response):
            day = response[key]
            day_res = []
            for para in day:
                if '---' in (para["audNum"]).rstrip():  # Экранирование множественных тире
                    para["audNum"] = "--"
                if '---' in (para["buildNum"]).rstrip():
                    para["buildNum"] = "--"
                para_structure = {
                    'dayDate': para["dayDate"][:100].rstrip(),
                    'disciplName': (para["disciplName"]).rstrip(),
                    'audNum': para["audNum"].rstrip(),
                    'buildNum': para["buildNum"].rstrip(),
                    'dayTime': para["dayTime"][:5].rstrip(),
                    'disciplType': para["disciplType"][:4].rstrip()
                }
                day_res.append(para_structure)
            res[int(key) - 1] = day_res
        return res

    @classmethod
    async def get_group_schedule(cls, group_id: int) -> list | None:
        try:
            response = await cls._get_schedule_data(group_id)
        except Exception:
            return None
        return cls._parse_schedule(response)

    @classmethod
    async def get_group_teachers(cls, group_id: int) -> list | None:
        try:
            response = await cls._get_schedule_data(group_id)
        except Exception:
            return None
        return cls._parse_teachers(response)


async def main():
    k = KaiParser()

    print(await k.get_group_ids())


if __name__ == '__main__':
    asyncio.run(main())
