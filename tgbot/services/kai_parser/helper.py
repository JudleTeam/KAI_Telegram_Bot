from datetime import datetime

from bs4 import BeautifulSoup

from tgbot.services.kai_parser.schemas import UserInfo, BaseUser, Group, Lesson, LessonType, Teacher, Documents
from tgbot.services.utils import parse_phone_number


def parse_teachers(response) -> list[Teacher]:
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
                if i.lesson_name == lesson_name and i.teacher_full_name == teacher_name.title():
                    if lesson_type not in i.type:
                        i.type += f', {lesson_type}'
                    break
            else:
                res.append(Teacher(lesson_type, lesson_name, teacher_name.title()))
    return res


def parse_schedule(response) -> list[list[Lesson]]:
    res = []  # by days with lessons
    for key in sorted(response):
        day = response[key]
        day_res = []
        for lesson in day:
            if '---' in (lesson["audNum"]).rstrip():  # Экранирование множественных тире
                lesson["audNum"] = "--"
            if '---' in (lesson["buildNum"]).rstrip():
                lesson["buildNum"] = "--"
            day_res.append(
                Lesson(
                    number_of_day=int(key),
                    start_time=lesson["dayTime"][:5].rstrip(),
                    parity_of_week=lesson["dayDate"][:100].rstrip(),
                    lesson_name=lesson["disciplName"].rstrip(),
                    auditory_number=lesson["audNum"].rstrip(),
                    building_number=lesson["buildNum"].rstrip(),
                    lesson_type=lesson["disciplType"][:4].rstrip()
                )
            )
        res.append(day_res)
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
    birthday = datetime.strptime(birthday_str, '%d.%m.%Y').date()

    phone = soup.find('input', id='_aboutMe_WAR_aboutMe10_phoneNumber0')['value'].strip()
    phone = parse_phone_number(phone)

    email = soup.find('input', id='_aboutMe_WAR_aboutMe10_email')['value'].strip().lower()

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
    last_table = soup.find_all('table')[-1]
    table_rows = last_table.find_all('tr')
    for ind, row in enumerate(table_rows[1:]):
        columns = row.find_all('td')

        full_name = columns[1].text.strip()
        if 'Староста' in full_name:
            leader_ind = ind
            full_name = full_name.replace('Староста', '').strip()
        email = columns[2].text.strip().lower()
        phone = parse_phone_number(columns[3].text.strip())

        user = BaseUser(full_name=full_name, email=email, phone=phone)
        group_members.append(user)

    return Group(members=group_members, leader_index=leader_ind)


def parse_documents(soup: BeautifulSoup) -> Documents:
    content = soup.find('div', class_='row div_container')
    urls = content.find_all('a', limit=3)

    return Documents(
        syllabus=urls[1]['href'],
        educational_program=urls[0]['href'],
        study_schedule=urls[2]['href']
    )
