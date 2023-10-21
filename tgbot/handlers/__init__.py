from .commands          import router as commands_router
from .errors            import router as errors_router
from .full_schedule     import router as full_schedule_router
from .other             import router as other_router
from .user              import router as user_router
from .main_menu         import router as main_menu_router
from .schedule          import router as schedule_router
from .teachers          import router as teachers_router
from .profile           import router as profile_router
from .group_choose      import router as group_choose_router
from .admin_commands    import router as admin_commands_router
from .verification      import router as verification_router
from .education         import router as education_router
from .my_group          import router as my_group_router
from .settings          import router as settings_router
from .details           import router as details_router

routers = (
    schedule_router,
    main_menu_router,
    commands_router,
    other_router,
    user_router,
    teachers_router,
    profile_router,
    education_router,
    my_group_router,
    group_choose_router,
    verification_router,
    admin_commands_router,
    settings_router,
    details_router,
    full_schedule_router,
    errors_router
)
