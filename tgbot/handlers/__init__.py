from .commands import register_commands
from .other import register_other
from .user import register_user
from .main_menu import register_main_menu
from .schedule import register_schedule

register_functions = (
    register_commands,
    register_other,
    register_user,
    register_main_menu,
    register_schedule
)
