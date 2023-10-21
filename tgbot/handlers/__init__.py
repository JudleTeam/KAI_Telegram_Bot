from .commands import commands_router
from .errors import router as errors_router
from .full_schedule import router as full_schedule_router
from .other import register_other
from .user import register_user
from .main_menu import router as main_menu_router
from .schedule import register_schedule
from .teachers import register_teachers
from .profile import register_profile
from .group_choose import router as group_choose_router
from .admin_commands import admin_commands_router
from .verification import register_verification
from .education import router as education_router
from .my_group import router as my_group_router
from .settings import register_settings
from .details import router as details_router

register_functions = (
    register_schedule,
    # register_main_menu,
    # register_commands,
    register_other,
    register_user,
    register_teachers,
    register_profile,
    # register_education,
    # register_my_group,
    # register_group_choose,
    register_verification,
    # register_admin_commands,
    register_settings,
    # register_details,
    # register_full_schedule,
    # register_errors
)

routers = (
    main_menu_router,
    commands_router,
    education_router,
    my_group_router,
    group_choose_router,
    admin_commands_router,
    details_router,
    full_schedule_router,
    errors_router
)
