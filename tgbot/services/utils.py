import phonenumbers
from phonenumbers import NumberParseException
from sqlalchemy.orm import Session

from tgbot.misc.texts import roles
from tgbot.services.database.models import KAIUser, Speciality, Departament, Institute, Profile, User, Role
from tgbot.services.kai_parser.schemas import FullUserData


def parse_phone_number(phone_number) -> str | None:
    """
    Parsing a phone number with an attempt to replace the first 8 with 7 and add 7 if it is not there, on error

    :param phone_number:
    :return: String phone number in E164 format or None if number is not vaild
    """
    phone_number = str(phone_number)
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    try:
        parsed_number = phonenumbers.parse(phone_number)
    except NumberParseException:
        phone_number = phone_number.replace('8', '7', 1)
        try:
            parsed_number = phonenumbers.parse(phone_number)
        except NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed_number):
        phone_number = phone_number.replace('+', '+7')
        try:
            parsed_number = phonenumbers.parse(phone_number)
        except NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed_number):
        return None

    return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)


async def add_full_user_to_db(full_user: FullUserData, login: str, password: str, tg_id: int, db: Session):
    user_about = full_user.user_about
    user_info = full_user.user_info

    contract_number = int(user_about.numDog) if user_about.numDog.isdigit() else None

    async with db.begin() as session:
        kai_user: KAIUser = await KAIUser.get_by_email(full_user.user_info.email, db)
        tg_user: User = await session.get(User, tg_id)
        speciality = await session.get(Speciality, int(user_about.specId))
        if not speciality:
            speciality = Speciality(id=int(user_about.specId), name=user_about.specName, code=user_about.specCode)
            session.add(speciality)

        departament = await session.get(Departament, int(user_about.kafId))
        if not departament:
            departament = Departament(id=int(user_about.kafId), name=user_about.kafName)
            session.add(departament)

        institute = await session.get(Institute, int(user_about.instId))
        if not institute:
            institute = Institute(id=int(user_about.instId), name=user_about.instName)
            session.add(institute)

        profile = await session.get(Profile, int(user_about.profileId))
        if not profile:
            profile = Profile(id=int(user_about.profileId), name=user_about.profileName)
            session.add(profile)

        if kai_user:
            kai_user.telegram_user_id = tg_id

            kai_user.kai_id = int(user_about.studId)
            kai_user.competition_type = user_about.competitionType
            kai_user.zach_number = int(user_about.zach)
            kai_user.contract_number = contract_number
            kai_user.edu_level = user_about.eduLevel
            kai_user.edu_cycle = user_about.eduCycle
            kai_user.edu_qualification = user_about.eduQualif
            kai_user.status = user_about.status.strip()
            kai_user.program_form = user_about.programForm

            kai_user.login = login
            kai_user.password = password
            kai_user.phone = user_info.phone
            kai_user.full_name = user_info.full_name
            kai_user.sex = user_info.sex
            kai_user.birthday = user_info.birthday

            kai_user.specialty = speciality
            kai_user.departament = departament
            kai_user.institute = institute
            kai_user.profile = profile

            await session.merge(kai_user)
        else:
            kai_user = KAIUser(
                kai_id=int(user_about.studId),
                telegram_user_id=tg_id,
                login=login,
                password=password,
                full_name=user_info.full_name,
                phone=user_info.phone,
                email=user_info.email,
                sex=user_info.sex,
                birthday=user_info.birthday,
                group_id=int(user_about.groupId),
                zach_number=int(user_about.zach),
                competition_type=user_about.competitionType,
                contract_number=contract_number,
                edu_level=user_about.eduLevel,
                edu_cycle=user_about.eduCycle,
                edu_qualification=user_about.eduQualif,
                program_form=user_about.programForm,
                status=user_about.status.strip(),
                specialty=speciality,
                profile=profile,
                departament=departament,
                institute=institute
            )
            session.add(kai_user)

        if not tg_user.has_role(roles.authorized):
            authorized_role = await Role.get_by_title(roles.authorized, db)
            tg_user.roles.append(authorized_role)

        leader_email = full_user.group.members[full_user.group.leader_index].email
        if leader_email == user_info.email and not tg_user.has_role(roles.group_leader):
            leader_role = await Role.get_by_title(roles.group_leader, db)
            tg_user.roles.append(leader_role)

        for member in full_user.group.members:
            if member.email == user_info.email:
                continue

            member_in_db = await KAIUser.get_by_email(member.email, db)
            if not member_in_db:
                new_member = KAIUser(
                    full_name=member.full_name,
                    phone=member.phone,
                    email=member.email,
                    group_id=int(user_about.groupId)
                )
                session.add(new_member)
