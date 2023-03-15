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

