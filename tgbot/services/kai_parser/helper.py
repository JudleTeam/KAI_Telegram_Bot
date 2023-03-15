from datetime import datetime

from bs4 import BeautifulSoup

from tgbot.services.kai_parser.schemas import UserInfo, Group, BaseUser
from tgbot.services.utils import parse_phone_number


def parse_teachers(response) -> list:
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


def parse_schedule(response) -> list:
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


def parse_user_info(soup: BeautifulSoup):
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


def parse_group_members(soup: BeautifulSoup) -> Group:
    group_members = list()
    leader_ind = None
    table_rows = soup.find_all('tr')
    for ind, row in enumerate(table_rows[1:]):
        columns = row.find_all('td')

        full_name = columns[1].text.strip()
        if 'Староста' in full_name:
            leader_ind = ind
            full_name = full_name.replace('Староста', '').strip()
        email = columns[2].text.strip()
        phone = parse_phone_number(columns[3].text.strip())

        user = BaseUser(full_name=full_name, email=email, phone=phone)
        group_members.append(user)

    return Group(members=group_members, leader_index=leader_ind)

