import json
import logging
from json import JSONDecodeError

import aiohttp
from aiohttp.abc import AbstractCookieJar
from bs4 import BeautifulSoup

from tgbot.services.kai_parser import helper
from tgbot.services.kai_parser.schemas import KaiApiError, UserAbout, FullUserData, Group, UserInfo, BadCredentials, \
    ParsingError


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
    async def get_user_info(cls, login, password, login_cookies=None) -> UserInfo:
        login_cookies = login_cookies or await cls._get_login_cookies(login, password)

        async with aiohttp.ClientSession(cookie_jar=login_cookies) as session:
            async with session.get(cls.about_me_url, headers=cls.base_headers) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from about me request')

                soup = BeautifulSoup(await response.text(), 'lxml')

        return helper.parse_user_info(soup)

    @classmethod
    async def get_user_about(cls, login, password, role='student', login_cookies=None) -> UserAbout | None:
        """
        API response example:
        list: [
            {
              "groupNum": "4115",
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
              "zach": "41241",
              "profileName": "Разработка программно-информационных систем",
              "dateDog": "",
              "kafId": "1264959",
              "rabTheme": ""
            }
        ]

        :param retries:
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
            raise KaiApiError(f'[{login}]: Failed decode received data. Part of text: {text[:32]}...')
        else:
            if user_data.get('list') is not None and len(user_data.get('list')) == 0:
                raise KaiApiError(f'[{login}]: No data')

            return UserAbout(**user_data['list'][-1])

    @classmethod
    async def get_full_user_data(cls, login, password) -> FullUserData:
        login = login.lower()

        login_cookies = await cls._get_login_cookies(login, password)

        user_info = await cls.get_user_info(login, password, login_cookies)
        user_about = await cls.get_user_about(login, password, login_cookies=login_cookies)
        user_group = await cls.get_user_group_members(login, password, login_cookies)

        full_user_data = FullUserData(
            user_info=user_info,
            user_about=user_about,
            group=user_group
        )

        return full_user_data

    @classmethod
    async def get_user_group_members(cls, login, password, login_cookies=None) -> Group:
        login_cookies = login_cookies or await cls._get_login_cookies(login, password)

        async with aiohttp.ClientSession(cookie_jar=login_cookies) as session:
            async with session.get(cls.my_group_url, headers=cls.base_headers) as response:
                if not response.ok:
                    raise KaiApiError(f'[{login}]: {response.status} received from my group request')
                soup = BeautifulSoup(await response.text(), 'lxml')

        return helper.parse_group_members(soup)

    @classmethod
    async def get_group_ids(cls) -> dict:
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
    async def get_group_schedule(cls, group_id: int) -> list | None:
        try:
            response = await cls._get_schedule_data(group_id)
        except Exception as e:
            logging.error(e)
            raise KaiApiError

        try:
            result = helper.parse_schedule(response)
        except Exception as e:
            logging.error(e)
            raise ParsingError
        return result

    @classmethod
    async def get_group_teachers(cls, group_id: int) -> list | None:
        try:
            response = await cls._get_schedule_data(group_id)
        except Exception as e:
            logging.error(e)
            raise KaiApiError

        try:
            result = helper.parse_teachers(response)
        except Exception as e:
            logging.error(e)
            raise ParsingError
        return result

    @classmethod
    async def _get_login_cookies(cls, login, password, retries=1) -> AbstractCookieJar | None:
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
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
            raise BadCredentials(f'[{login}]: Login failed. Invalid login or password')
        logging.error(f'[{login}]: Login failed. Retry {retries}')
        return await cls._get_login_cookies(login, password, retries + 1)

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
