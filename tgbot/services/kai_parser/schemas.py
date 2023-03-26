import datetime
from dataclasses import dataclass


class KaiApiError(Exception):
    """Can't get data from Kai site"""


class BadCredentials(Exception):
    """Bad credentials for login"""


@dataclass
class Teacher:
    type: str
    lesson_name: str
    teacher_full_name: str


@dataclass
class BaseUser:
    full_name: str
    phone: str | None
    email: str


@dataclass
class UserInfo(BaseUser):
    sex: str
    birthday: datetime.date


@dataclass
class UserAbout:
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
    zach: int
    profileName: str
    dateDog: str | None
    kafId: int
    rabTheme: str | None


@dataclass
class Group:
    members: list[BaseUser]
    leader_index: int | None


@dataclass
class FullUserData:
    user_info: UserInfo
    user_about: UserAbout
    group: Group
