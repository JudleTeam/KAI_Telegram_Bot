import asyncio
import json
import logging
from json import JSONDecodeError

import aiohttp
from aiohttp import CookieJar
from aiohttp.abc import AbstractCookieJar
from sqlalchemy.exc import IntegrityError

from tgbot.services.database.models import Group
from tgbot.services.kai_parser.schemas import KaiApiError


class KaiParser:
    base_url = 'https://kai.ru/raspisanie'
    login_url = 'https://kai.ru/main?p_p_id=58&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&_58_struts_action=/login/login'
    about_me_url = 'https://kai.ru/group/guest/common/about-me?p_p_id=aboutMe_WAR_aboutMe10&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getRoleData&p_p_cacheability=cacheLevelPage&p_p_col_id=column-2&p_p_col_count=1'
    kai_url = 'https://kai.ru/main'

    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    @classmethod
    async def _get_schedule_data(cls, group_id: int) -> list:
        async with aiohttp.ClientSession() as session:
            async with session.post(cls.base_url, data="groupId=" + str(group_id),
                                    headers=cls.base_headers,
                                    params={"p_p_id": "pubStudentSchedule_WAR_publicStudentSchedule10",
                                            "p_p_lifecycle": "2", "p_p_resource_id": "schedule"},
                                    timeout=3) as response:
                response = await response.json(content_type='text/html')
                return response

    @classmethod
    async def _get_login_cookies(cls, login, password) -> AbstractCookieJar | None:
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Host': 'kai.ru',
            'Origin': 'https://kai.ru',
            'Referer': 'https://kai.ru/main',
            'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,ru;q =0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(cls.kai_url, headers=login_headers) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from "{cls.kai_url}"')
            cookies = session.cookie_jar

        login_data = {
            '_58_login': login,
            '_58_password': password
        }
        async with aiohttp.ClientSession(cookie_jar=cookies) as session:
            async with session.post(cls.login_url, data=login_data, headers=login_headers, timeout=20) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from login request')

        for el in session.cookie_jar:
            if el.key == 'USER_UUID':
                return session.cookie_jar

    @classmethod
    async def _login_session(cls, session: aiohttp.ClientSession, login, password) -> bool:
        """
        ТУПОЕ ГОВНО ГОВНА ВТОРОЙ ЗАПРОС ПРОСТО ПАДАЕТ С TIMEOUT ERROR ХУЙ ПОЙМИ С ЧЕГО РАЗРАБЫ ДАУНЫ. С ОТДЕЛЬЫНМИ
        СЕССИЯМИ ВСЁ РАБОТАЕТ ПРЕКРАСНО, А ТУТ ТОЛЬКО ЕСЛИ ЗАПУСКАТЬ В ДЕБАГЕ И ТО ЧЕРЕЗ РАЗ НАХУЙ

        :param session:
        :param login:
        :param password:
        :return:
        """
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Host': 'kai.ru',
            'Origin': 'https://kai.ru',
            'Referer': 'https://kai.ru/main',
            'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,ru;q =0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with session.get(cls.kai_url, headers=login_headers) as response:
            print(response.status)
            if not response.ok:
                raise KaiApiError(f'[{login}]: {response.status} received from "{cls.kai_url}"')

        print([el for el in session.cookie_jar])

        login_data = {
            '_58_login': login,
            '_58_password': password
        }
        await asyncio.sleep(1)
        print(1)
        async with session.post(cls.login_url, data=login_data, headers=login_headers, timeout=20) as response:
            print(response.status)
            if not response.ok:
                raise KaiApiError(f'[{login}]: {response.status} received from login request')

        print([el for el in session.cookie_jar])
        for el in session.cookie_jar:
            if el.key == 'USER_UUID':
                return True

        return False

    @classmethod
    async def get_user_about(cls, login, password, role='student', login_retries=3) -> dict | None:
        """
        Result example:
        {
          "groupNum": "4111",
          "competitionType": "бюджет",
          "specCode": "09.03.04 Программная инженерия",
          "kafName": "Кафедра прикладной математики и информатики",
          "programForm": "Очная",
          "profileId": "698",
          "numDog": "",
          "rukFio": "",
          "eduLevel": "1 высшее",
          "rabProfile": "",
          "oval": "",
          "eduQualif": "Бакалавр",
          "predpr": "",
          "status": "Студент             ",
          "instId": "1264871",
          "studId": "168971",
          "instName": "Институт компьютерных технологий и защиты информации",
          "tabName": "Студент             ",
          "groupId": "23542",
          "eduCycle": "Полный",
          "specName": "Программная инженерия",
          "specId": "1540001",
          "zach": "241287",
          "profileName": "Разработка программно-информационных систем",
          "dateDog": "",
          "kafId": "1264959",
          "rabTheme": ""
        }

        :param login:
        :param password:
        :param role:
        :param login_retries:
        :return:
        """
        for _ in range(login_retries):
            login_cookies = await cls._get_login_cookies(login, password)
            if login_cookies:
                break
        else:
            raise KaiApiError(f'[{login}]: Login failed after {login_retries} retries')

        async with aiohttp.ClientSession(cookie_jar=login_cookies) as session:
            # result = await cls._login_session(session, login, password)
            # if not result:
            #     raise KaiApiError(f'[{login}]: Login failed')

            about_me_data = {
                'login': login,
                'tab': role
            }

            async with session.post(cls.about_me_url, headers=cls.base_headers, data=about_me_data) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from about me request')
                text = await response.text()

            text = text.strip()
            try:
                user_data = json.loads(text)
            except JSONDecodeError:
                logging.error(f'[{login}]: Failed decode received data. Part of text: {text[:32]}...')
                return None
            else:
                if user_data.get('list') is not None and len(user_data.get('list')) == 0:
                    return None

                return user_data

    @classmethod
    async def get_group_ids(cls) -> list:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    cls.base_url + "?p_p_id=pubStudentSchedule_WAR_publicStudentSchedule10&p_p_lifecycle=2"
                                   "&p_p_resource_id=getGroupsURL&query=",
                    headers=cls.base_headers,
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

    print(await k.get_user_about('KitaevGA', 'pass'))


if __name__ == '__main__':
    asyncio.run(main())
