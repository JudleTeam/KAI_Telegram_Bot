import logging

from sqlalchemy.orm import Session

from tgbot.misc.texts import roles
from tgbot.services.database.models import Role, KAIUser, User, Speciality, Departament, Profile, Institute, Group
from tgbot.services.kai_parser.schemas import FullUserData
from tgbot.services.utils.other import parse_phone_number


async def add_full_user_to_db(full_user: FullUserData, login: str, password: str, tg_id: int, db: Session) -> bool:
    user_about = full_user.user_about
    user_info = full_user.user_info

    roles_dict = await Role.get_roles_dict(db)
    prefix = None

    async with db.begin() as session:
        kai_user: KAIUser = await KAIUser.get_by_email(session, full_user.user_info.email)
        already_used = bool(kai_user.telegram_user_id) if kai_user else False
        tg_user: User = await session.get(User, tg_id)

        speciality = await Speciality.get_or_create(session, user_about.specId, user_about.specName, user_about.specCode)
        departament = await Departament.get_or_create(session, user_about.kafId, user_about.kafName)
        institute = await Institute.get_or_create(session, user_about.instId, user_about.instName)
        profile = await Profile.get_or_create(session, user_about.profileId, user_about.profileName)

        if not already_used:
            if not tg_user.has_role(roles.authorized):
                tg_user.roles.append(roles_dict[roles.authorized])

            if not tg_user.has_role(roles.verified):
                tg_user.roles.append(roles_dict[roles.verified])

            is_leader = False
            leader_email = full_user.group.members[full_user.group.leader_num - 1].email
            if leader_email == user_info.email and not tg_user.has_role(roles.group_leader):
                tg_user.roles.append(roles_dict[roles.group_leader])
                is_leader = True
                prefix = '👨🏻‍💼'
                logging.info(f'[{tg_id}]: Appointed group leader')

        if kai_user:
            if not already_used:
                kai_user.telegram_user_id = tg_id
                kai_user.is_leader = is_leader

            kai_user.kai_id = user_about.studId
            kai_user.competition_type = user_about.competitionType
            kai_user.zach_number = user_about.zach
            kai_user.contract_number = user_about.numDog
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

            kai_user.group.speciality = speciality
            kai_user.group.departament = departament
            kai_user.group.institute = institute
            kai_user.group.profile = profile

            kai_user.group.syllabus = full_user.documents.syllabus
            kai_user.group.educational_program = full_user.documents.educational_program
            kai_user.group.study_schedule = full_user.documents.study_schedule

            kai_user = await session.merge(kai_user)
        else:
            insert_tg_id = None if already_used else tg_id
            kai_user = KAIUser(
                kai_id=user_about.studId,
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
                group_id=user_about.groupId,
                zach_number=user_about.zach,
                competition_type=user_about.competitionType,
                contract_number=user_about.numDog,
                edu_level=user_about.eduLevel,
                edu_cycle=user_about.eduCycle,
                edu_qualification=user_about.eduQualif,
                program_form=user_about.programForm,
                status=user_about.status.strip(),
            )

            group = await session.get(Group, user_about.groupId)
            group.syllabus = full_user.documents.syllabus
            group.educational_program = full_user.documents.educational_program
            group.study_schedule = full_user.documents.study_schedule

            group.speciality = speciality
            group.departament = departament
            group.institute = institute
            group.profile = profile

            session.add(kai_user)

        await update_group_members(session, full_user, kai_user, roles_dict, tg_id)

    return not already_used


async def update_group_members(session, full_user: FullUserData, kai_user: KAIUser, roles_dict: dict, tg_id: int):
    for num, member in enumerate(full_user.group.members, start=1):
        if member.email == full_user.user_info.email:
            kai_user.position = num
            await session.merge(kai_user)
            continue

        member_tg_id = None
        if member.phone:
            member_tg: User = await User.get_by_phone(session, member.phone)
            if member_tg and not member_tg.has_role(roles.verified):
                member_tg_id = member_tg.telegram_id
                member_tg.roles.append(roles_dict[roles.verified])
                await session.merge(member_tg)

                logging.info(f'[{tg_id}]: Verified classmate {member_tg_id}')

        member_in_db = await KAIUser.get_by_email(session, member.email)
        if not member_in_db:
            is_mem_leader = num == full_user.group.leader_num
            new_member = KAIUser(
                telegram_user_id=member_tg_id,
                full_name=member.full_name,
                phone=member.phone,
                email=member.email,
                is_leader=is_mem_leader,
                prefix='👨🏻‍💼' if is_mem_leader else None,
                position=num,
                group_id=full_user.user_about.groupId
            )
            session.add(new_member)


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
