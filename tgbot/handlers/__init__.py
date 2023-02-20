from .commands import register_commands
from .other import register_other
from .user import register_user
from .main_menu import register_main_menu
from .schedule import register_schedule
from .teachers import register_teachers
from .profile import register_profile
from .group_choose import register_group_choose

register_functions = (
    register_commands,
    register_other,
    register_user,
    register_main_menu,
    register_schedule,
    register_teachers
    register_profile,
    register_group_choose
)
