from .commands import register_commands
from .other import register_other
from .user import register_user

register_functions = (
    register_commands,
    register_other,
    register_user
)
