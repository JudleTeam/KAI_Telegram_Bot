import logging

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


async def add_full_user_to_db(full_user: FullUserData, login: str, password: str, tg_id: int, db: Session) -> bool:
    user_about = full_user.user_about
    user_info = full_user.user_info

    contract_number = int(user_about.numDog) if user_about.numDog.isdigit() else None
    roles_dict = await Role.get_roles_dict(db)
    prefix = None

    async with db.begin() as session:
        kai_user: KAIUser = await KAIUser.get_by_email(full_user.user_info.email, db)
        already_used = bool(kai_user.telegram_user_id) if kai_user else False
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

        if not already_used:
            if not tg_user.has_role(roles.authorized):
                tg_user.roles.append(roles_dict[roles.authorized])

            if not tg_user.has_role(roles.verified):
                tg_user.roles.append(roles_dict[roles.verified])

            is_leader = False
            leader_email = full_user.group.members[full_user.group.leader_index].email
            if leader_email == user_info.email and not tg_user.has_role(roles.group_leader):
                tg_user.roles.append(roles_dict[roles.group_leader])
                is_leader = True
                prefix = '👨🏻‍💼'
                logging.info(f'[{tg_id}]: Appointed group leader')

        if kai_user:
            if not already_used:
                kai_user.telegram_user_id = tg_id
                kai_user.is_leader = is_leader

            kai_user.kai_id = int(user_about.studId)
            kai_user.competition_type = user_about.competitionType
            kai_user.zach_number = int(user_about.zach)
            kai_user.contract_number = contract_number
            kai_user.edu_level = user_about.eduLevel
            kai_user.edu_cycle = user_about.eduCycle
            kai_user.edu_qualification = user_about.eduQualif
            kai_user.status = user_about.status.strip()
            kai_user.program_form = user_about.programForm

            kai_user.prefix = prefix
            kai_user.login = login
            kai_user.password = password
            kai_user.phone = user_info.phone
            kai_user.full_name = user_info.full_name
            kai_user.sex = user_info.sex
            kai_user.birthday = user_info.birthday

            kai_user.speciality = speciality
            kai_user.departament = departament
            kai_user.institute = institute
            kai_user.profile = profile

            kai_user = await session.merge(kai_user)
        else:
            insert_tg_id = None if already_used else tg_id
            kai_user = KAIUser(
                kai_id=int(user_about.studId),
                telegram_user_id=insert_tg_id,
                login=login,
                password=password,
                full_name=user_info.full_name,
                phone=user_info.phone,
                email=user_info.email,
                sex=user_info.sex,
                birthday=user_info.birthday,
                is_leader=is_leader,
                prefix=prefix,
                group_id=int(user_about.groupId),
                zach_number=int(user_about.zach),
                competition_type=user_about.competitionType,
                contract_number=contract_number,
                edu_level=user_about.eduLevel,
                edu_cycle=user_about.eduCycle,
                edu_qualification=user_about.eduQualif,
                program_form=user_about.programForm,
                status=user_about.status.strip(),
                speciality=speciality,
                profile=profile,
                departament=departament,
                institute=institute
            )
            session.add(kai_user)

        for ind, member in enumerate(full_user.group.members):
            if member.email == user_info.email:
                kai_user.position = ind + 1
                await session.merge(kai_user)
                continue

            if member.phone:
                member_tg: User = await User.get_by_phone(member.phone, db)
                if member_tg and not member_tg.has_role(roles.verified):
                    member_tg_id = member_tg.telegram_id
                    member_tg.roles.append(roles_dict[roles.verified])
                    await session.merge(member_tg)

                    logging.info(f'[{tg_id}]: Verified classmate {member_tg_id}')
                else:
                    member_tg_id = None

            member_in_db = await KAIUser.get_by_email(member.email, db)
            if not member_in_db:
                is_mem_leader = ind == full_user.group.leader_index
                new_member = KAIUser(
                    telegram_user_id=member_tg_id,
                    full_name=member.full_name,
                    phone=member.phone,
                    email=member.email,
                    is_leader=is_mem_leader,
                    prefix='👨🏻‍💼' if is_mem_leader else None,
                    position=ind + 1,
                    group_id=int(user_about.groupId)
                )
                session.add(new_member)

    return not already_used


async def verify_profile_with_phone(telegram_id: int, phone: str, db: Session) -> bool | None:
    phone = parse_phone_number(phone)
    is_verified = False
    async with db() as session:
        user = await session.get(User, telegram_id)
        user.phone = phone

        await session.commit()
        kai_user = await KAIUser.get_by_phone(phone, db)
        if kai_user:
            if kai_user.telegram_user_id and kai_user.telegram_user_id != telegram_id:
                return None
            kai_user.telegram_user_id = telegram_id
            await session.merge(kai_user)

            if not user.has_role(roles.verified):
                verified_role = await Role.get_by_title(roles.verified, db)
                user.roles.append(verified_role)

            await session.commit()

            is_verified = True

    return is_verified
