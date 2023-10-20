import asyncio
import json
import logging
from json import JSONDecodeError
from pprint import pprint

import aiohttp
from aiohttp import CookieJar
from aiohttp.abc import AbstractCookieJar
from bs4 import BeautifulSoup

from tgbot.services.kai_parser import helper
from tgbot.services.kai_parser.schemas import (KaiApiError, UserAbout, FullUserData, Group, UserInfo, BadCredentials,
                                               ParsingError, Documents, Teacher, GroupsResult, Lesson)


class KaiParser:
    base_url = 'https://kai.ru/raspisanie'
    about_me_url = 'https://kai.ru/group/guest/common/about-me'
    my_group_url = 'https://kai.ru/group/guest/student/moa-gruppa'
    kai_main_url = 'https://kai.ru/main'
    syllabus_url = 'https://kai.ru/group/guest/student/ucebnyj-plan'

    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    _timeout = 30

    @classmethod
    async def _request(
            cls,
            method: str,
            url: str,
            requires_login: bool = False,
            login_cookies: CookieJar | None = None,
            login: str | None = None,
            password: str | None = None,
            return_soup: bool = False,
            return_text: bool = False,
            return_json: bool = False,
            **kwargs
    ):

        if method not in ('POST', 'GET', 'PUT', 'DELETE', 'PATCH'):
            raise ValueError(f'Unknown method "{method}"')

        if requires_login and not login_cookies:
            login_cookies = await cls._get_login_cookies(login, password)

        async with aiohttp.ClientSession(headers=cls.base_headers, cookie_jar=login_cookies) as session:
            match method:
                case 'POST':
                    request = session.post
                case 'GET':
                    request = session.get
                case 'PUT':
                    request = session.put
                case 'DELETE':
                    request = session.delete
                case 'PATCH':
                    request = session.patch

            try:
                async with request(url, timeout=cls._timeout, **kwargs) as response:
                    if not response.ok:
                        raise KaiApiError(f'{login or ""} {response.status} received from "{url}"')

                    if return_soup:
                        return BeautifulSoup(await response.text(), 'lxml')

                    if return_text:
                        return await response.text()

                    if return_json:
                        return await response.json(content_type='text/html')

                    return response

            except asyncio.TimeoutError:
                raise KaiApiError(f'Timeout error received from "{url}"')

    @classmethod
    async def get_documents(cls, login, password, login_cookies=None) -> Documents:
        """Need fix"""
        soup = await cls._request('GET', cls.syllabus_url, True, login_cookies=login_cookies,
                                  login=login, password=password, return_soup=True)

        return helper.parse_documents(soup)

    @classmethod
    async def get_user_info(cls, login, password, login_cookies=None) -> UserInfo:
        soup = await cls._request('GET', cls.about_me_url, True, login_cookies=login_cookies,
                                  login=login, password=password, return_soup=True)

        return helper.parse_user_info(soup)

    @classmethod
    async def get_user_about(cls, login, password, login_cookies=None) -> UserAbout | None:
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

        :param login_cookies:
        :param login:
        :param password:
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
        about_me_data = {
            'login': login,
            'tab': 'student'
        }

        text = await cls._request('POST', cls.about_me_url, requires_login=True, login_cookies=login_cookies,
                                  login=login, password=password, return_text=True, data=about_me_data,
                                  params=request_params)

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
        documents = await cls.get_documents(login, password, login_cookies)

        full_user_data = FullUserData(
            user_info=user_info,
            user_about=user_about,
            group=user_group,
            documents=documents
        )

        return full_user_data

    @classmethod
    async def get_user_group_members(cls, login, password, login_cookies=None) -> Group:
        soup = await cls._request('GET', cls.my_group_url, True, login_cookies=login_cookies,
                                  login=login, password=password, return_soup=True)

        return helper.parse_group_members(soup)

    @classmethod
    async def get_group_ids(cls) -> list[GroupsResult]:
        params = {
            'p_p_id': 'pubStudentSchedule_WAR_publicStudentSchedule10',
            'p_p_lifecycle': 2,
            'p_p_resource_id': 'getGroupsURL'
        }

        result = await cls._request('POST', cls.base_url, params=params, return_json=True)
        return [GroupsResult(**group) for group in result]

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
    async def get_group_schedule(cls, group_id: int) -> list[Lesson]:
        params = {
            'p_p_id': 'pubStudentSchedule_WAR_publicStudentSchedule10',
            'p_p_lifecycle': 2,
            'p_p_resource_id': 'schedule'
        }
        data = {
            'groupId': group_id
        }

        result = await cls._request('POST', cls.base_url, data=data, params=params, return_json=True)
        return [Lesson(**lesson) for day_lessons in result.values() for lesson in day_lessons]

