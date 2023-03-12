import asyncio
import datetime
import json
import logging
from json import JSONDecodeError

import aiohttp
from aiohttp.abc import AbstractCookieJar
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError

from tgbot.services.database.models import Group
from tgbot.services.kai_parser.schemas import KaiApiError, UserAbout, UserInfo, FullUserData, BaseUser
from tgbot.services.utils import parse_phone_number


class KaiParser:
    base_url = 'https://kai.ru/raspisanie'
    about_me_url = 'https://kai.ru/group/guest/common/about-me'
    my_group_url = 'https://kai.ru/group/guest/student/moa-gruppa'
    kai_main_url = 'https://kai.ru/main'

    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    _timeout = 10

    @classmethod
    async def _get_schedule_data(cls, group_id: int) -> list:
        params = {
            'p_p_id': 'pubStudentSchedule_WAR_publicStudentSchedule10',
            'p_p_lifecycle': 2,
            'p_p_resource_id': 'schedule'
        }
        data = {
            'groupId': group_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(cls.base_url, data=data, headers=cls.base_headers,
                                    params=params, timeout=cls._timeout) as response:
                response = await response.json(content_type='text/html')
                return response

    @classmethod
    async def _get_login_cookies(cls, login, password, retries=1) -> AbstractCookieJar | None:
        login_headers = {
            'User-Agent': 'KAI_PUP',
            'Host': 'kai.ru',
            'Origin': 'https://kai.ru',
            'Referer': 'https://kai.ru/',
            'Accept': 'text/html,application/xhtml+xml, application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,ru;q =0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(cls.kai_main_url, headers=login_headers) as response:
                if not response.ok:
                    if retries > 3:
                        raise KaiApiError(f'[{login}]: {response.status} received from "{cls.kai_main_url}"')
                    logging.error(f'[{login}]: Bad response from KAI. Retry {retries}')
                    return await cls._get_login_cookies(login, password, retries + 1)
            cookies = session.cookie_jar

        login_data = {
            '_58_login': login,
            '_58_password': password
        }
        login_params = {
            'p_p_id': 58,
            'p_p_lifecycle': 1,
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_58_struts_action': '/login/login'
        }
        async with aiohttp.ClientSession(cookie_jar=cookies) as session:
            await session.post(cls.kai_main_url, data=login_data, headers=login_headers,
                               params=login_params, timeout=cls._timeout)

        for el in session.cookie_jar:
            if el.key == 'USER_UUID':
                return session.cookie_jar

        if retries > 3:
            return None
        logging.error(f'[{login}]: Login failed. Retry {retries}')
        return await cls._get_login_cookies(login, password, retries + 1)

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

        async with session.get(cls.kai_main_url, headers=login_headers) as response:
            print(response.status)
            if not response.ok:
                raise KaiApiError(f'[{login}]: {response.status} received from "{cls.kai_main_url}"')

        print([el for el in session.cookie_jar])

        login_data = {
            '_58_login': login,
            '_58_password': password
        }
        await asyncio.sleep(1)
        print(1)
        async with session.post(cls.kai_main_url, data=login_data, headers=login_headers,
                                timeout=cls._timeout) as response:
            print(response.status)
            if not response.ok:
                raise KaiApiError(f'[{login}]: {response.status} received from login request')

        print([el for el in session.cookie_jar])
        for el in session.cookie_jar:
            if el.key == 'USER_UUID':
                return True

        return False

    @classmethod
    async def get_user_info(cls, login, password, login_cookies=None):
        login_cookies = login_cookies or await cls._get_login_cookies(login, password)

        async with aiohttp.ClientSession(cookie_jar=login_cookies) as session:
            async with session.get(cls.about_me_url, headers=cls.base_headers) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from about me request')

                soup = BeautifulSoup(await response.text(), 'lxml')

        return cls._parse_user_info(soup)

    @classmethod
    def _parse_user_info(cls, soup: BeautifulSoup):
        last_name = soup.find('input', id='_aboutMe_WAR_aboutMe10_lastName')['value'].strip()
        first_name = soup.find('input', id='_aboutMe_WAR_aboutMe10_firstName')['value'].strip()
        middle_name = soup.find('input', id='_aboutMe_WAR_aboutMe10_middleName')['value'].strip()

        full_name = ' '.join((last_name, first_name, middle_name))

        sex = ''
        sex_select = soup.find('select', id='_aboutMe_WAR_aboutMe10_sex')
        for option in sex_select.findAll():
            if option.get('selected') is not None:
                sex = option.text.strip()
                break

        birthday_str = soup.find('input', id='_aboutMe_WAR_aboutMe10_birthDay')['value'].strip()
        birthday = datetime.datetime.strptime(birthday_str, '%d.%m.%Y').date()

        phone = soup.find('input', id='_aboutMe_WAR_aboutMe10_phoneNumber0')['value'].strip()
        phone = parse_phone_number(phone)

        email = soup.find('input', id='_aboutMe_WAR_aboutMe10_email')['value'].strip()

        user_info = UserInfo(
            full_name=full_name,
            sex=sex,
            birthday=birthday,
            phone=phone,
            email=email
        )

        return user_info

    @classmethod
    async def get_user_about(cls, login, password, role='student', login_cookies=None) -> UserAbout | None:
        """
        API response example:
        list: [
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
        ]

        :param login_cookies:
        :param login:
        :param password:
        :param role: Of the possible roles, only "student" is known
        :return:
        """
        request_params = {
            'p_p_id': 'aboutMe_WAR_aboutMe10',
            'p_p_lifecycle': 2,
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_resource_id': 'getRoleData',
            'p_p_cacheability': 'cacheLevelPage',
            'p_p_col_id': 'column-2',
            'p_p_col_count': 1
        }

        login_cookies = login_cookies or await cls._get_login_cookies(login, password)

        async with aiohttp.ClientSession(cookie_jar=login_cookies) as session:
            about_me_data = {
                'login': login,
                'tab': role
            }
            async with session.post(cls.about_me_url, headers=cls.base_headers,
                                    data=about_me_data, params=request_params) as response:
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

            return UserAbout(**user_data['list'][0])

    @classmethod
    async def get_full_user_data(cls, login, password) -> FullUserData:
        login_cookies = await cls._get_login_cookies(login, password)

        user_info = await cls.get_user_info(login, password, login_cookies)
        user_about = await cls.get_user_about(login, password, login_cookies=login_cookies)
        group_members = await cls.get_user_group_members(login, password, login_cookies)

        full_user_data = FullUserData(
            user_info=user_info,
            user_about=user_about,
            group_members=group_members
        )

        return full_user_data

    @classmethod
    async def get_user_group_members(cls, login, password, login_cookies=None):
        login_cookies = login_cookies or await cls._get_login_cookies(login, password)

        async with aiohttp.ClientSession(cookie_jar=login_cookies) as session:
            async with session.get(cls.my_group_url, headers=cls.base_headers) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from my group request')
                soup = BeautifulSoup(await response.text(), 'lxml')

        return cls._parse_group_members(soup)

    @classmethod
    def _parse_group_members(cls, soup: BeautifulSoup) -> list[BaseUser]:
        group_members = list()
        table_rows = soup.find_all('tr')
        for row in table_rows[1:]:
            columns = row.find_all('td')

            full_name = columns[1].text.strip()
            if 'Староста' in full_name:
                full_name = full_name.replace('Староста', '').strip()
            email = columns[2].text.strip()
            phone = parse_phone_number(columns[3].text.strip())

            user = BaseUser(full_name=full_name, email=email, phone=phone)
            group_members.append(user)

        return group_members

    @classmethod
    async def get_group_ids(cls) -> list:
        params = {
            'p_p_id': 'pubStudentSchedule_WAR_publicStudentSchedule10',
            'p_p_lifecycle': 2,
            'p_p_resource_id': 'getGroupsURL'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(cls.base_url, headers=cls.base_headers,
                                    params=params, timeout=cls._timeout) as response:
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

    full_data = await k.get_full_user_data('KitaevGA', 'pass')
    for user in full_data.group_members:
        print(user)
    # print(await k.get_group_ids())


if __name__ == '__main__':
    asyncio.run(main())
