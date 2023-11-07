schedule_day_template = (
    '               {day_of_week}\n'
    '————————————————\n'
    '{lessons}'
    '————————————————\n\n'
)

teacher_lesson = (
    '{start_time} - {end_time}  |  {building} {auditory} | {parity}\n'
    '{lesson_type} - {lesson_name}\n'
    '{group_names}'
)

lesson_template = (
    '{start_time} - {end_time}  |  {building} {auditory} | {parity}\n'
    '{lesson_type} - {lesson_name}{homework}{teacher}'
)

teacher_in_schedule = '\n{name} | {departament}'

teacher = (
    '{lesson_name} [{lesson_types}]\n'
    '{full_name}\n'
    '{departament}\n'
    '————————————————\n'
)

week_day = (
    '{pointer}{day} {date}'
)
