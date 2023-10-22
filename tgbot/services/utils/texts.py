from aiogram.types import User as aUser
from aiogram.utils import markdown as md
from aiogram.utils.i18n import gettext as _

from tgbot.misc.texts import messages, roles
from tgbot.services.database.models import User as dUser


def get_user_description(tg_user: aUser, db_user: dUser, for_admin=False):
    s_group = md.hcode(db_user.group.group_name) if db_user.group else '????'
    roles_str = ', '.join(map(_, db_user.get_roles_titles()))

    if for_admin:
        text = _(messages.for_admin_info).format(
            roles=roles_str,
            s_group_name=s_group,
            is_blocked=db_user.is_blocked,
            telegram_id=md.hcode(tg_user.id),
            tg_full_name=md.hcode(tg_user.full_name),
            tg_mention=md.hcode(tg_user.mention),
            telegram_phone=md.hcode(db_user.phone)
        )
    else:
        text = _(messages.profile_menu).format(roles=roles_str, s_group_name=s_group)

    if db_user.has_role(roles.verified):
        text += '\n\n' + _(messages.verified_info).format(
            full_name=md.hcode(db_user.kai_user.full_name),
            group_pos=md.hcode(db_user.kai_user.position),
            n_group_name=md.hcode(db_user.kai_user.group.group_name),
            phone=md.hcode(db_user.kai_user.phone or _(messages.missing)),
            email=md.hcode(db_user.kai_user.email)
        )

    if db_user.has_role(roles.authorized):
        text += '\n' + _(messages.authorized_info).format(zach=md.hcode(db_user.kai_user.zach_number),
                                                          birthday=db_user.kai_user.birthday)

    return text
