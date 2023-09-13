schedule_day_template = (
    '               {day_of_week}\n'
    '————————————————\n'
    '{lessons}'
    '————————————————\n\n'
)

lesson_template = (
    '{start_time} - {end_time}  |  {building} {auditory} | {parity}\n{lesson_type} - {lesson_name}'
)

teacher = (
    '{lesson_name} [{lesson_types}]\n'
    '{full_name}\n'
    '{departament}\n'
    '————————————————\n'
)

week_day = (
    '{pointer}{day} {date}'
)
