from dataclasses import dataclass


class KaiApiError(Exception):
    """Can't get data from Kai site"""


@dataclass
class Teacher:
    type: str
    lesson_name: str
    teacher_full_name: str
