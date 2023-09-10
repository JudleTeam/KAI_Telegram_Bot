import datetime
from pydantic import BaseModel, field_validator


class KaiApiError(Exception):
    """Can't get data from Kai site"""


class ParsingError(Exception):
    """Can't parse data from kai.ru"""


class BadCredentials(Exception):
    """Bad credentials for login"""


class GroupsResult(BaseModel):
    forma: str
    group: str
    id: int


class Teacher(BaseModel):
    type: str
    lesson_name: str
    teacher_full_name: str


class LessonType(str):
    lecture = 'лек'
    practice = 'пр'
    laboratory_work = 'л.р.'
    consultation = 'конс'


class Lesson(BaseModel):
    dayNum: int
    dayTime: datetime.time
    dayDate: str
    disciplName: str
    audNum: str
    buildNum: str
    disciplType: str
    disciplNum: int
    orgUnitId: int
    prepodName: str
    prepodLogin: str
    orgUnitName: str

    @field_validator('audNum')
    @classmethod
    def remove_dashes(cls, add_num: str):
        return add_num.replace('-', '')

    @field_validator('prepodName')
    @classmethod
    def title_teacher_name(cls, prepod_name: str):
        return prepod_name.title()

    @field_validator('dayTime', mode='before')
    @classmethod
    def convert_time(cls, day_time: str):
        return datetime.datetime.strptime(day_time.strip(), '%H:%M').time()

    class Config:
        str_strip_whitespace = True


class BaseUser(BaseModel):
    full_name: str
    phone: str | None
    email: str


class UserInfo(BaseUser):
    sex: str
    birthday: datetime.date


class UserAbout(BaseModel):
    groupNum: int
    competitionType: str
    specCode: str
    kafName: str
    programForm: str
    profileId: int
    numDog: int | None
    rukFio: str | None
    eduLevel: str
    rabProfile: str | None
    oval: str | None
    eduQualif: str
    predpr: str | None
    status: str
    instId: int
    studId: int
    instName: str
    tabName: str
    groupId: int
    eduCycle: str
    specName: str
    specId: int
    zach: str
    profileName: str
    dateDog: str | None
    kafId: int
    rabTheme: str | None

    @field_validator('numDog', mode='before')
    @classmethod
    def validate_num_dog(cls, num_dog: str):
        num_dog = num_dog.strip()
        if not num_dog.isdigit():
            return None
        return int(num_dog)

    class Config:
        str_strip_whitespace = True


class Group(BaseModel):
    members: list[BaseUser]
    leader_num: int | None


class Documents(BaseModel):
    syllabus: str
    educational_program: str
    study_schedule: str


class FullUserData(BaseModel):
    user_info: UserInfo
    user_about: UserAbout
    group: Group
    documents: Documents
