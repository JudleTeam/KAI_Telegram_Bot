from tgbot.misc.texts import _

welcome = _(f'Welcome to KAI bot! Tap button below to choose your language')
main_menu = _('Main menu')

language_changed = _('Language changed')

spam_block = _('You have been blocked for spam!')
spam_unblock = _('Unlocked, you can continue to use the bot.')

user_unregistered = _('It looks like you aren\'t registered in the bot. Type "/start" to fix it.')
user_blocked = _('You are blocked in the bot! If this is an error, contact the administrator.')

language_not_available = _('The language you are using is no longer available. '
                           'Contact the administrator or change the language.')
language_choose = _('Please select your language.')

schedule_menu = _(
    'Schedule menu\n'
    'Now {week} week\n\n'
    '🧪 - Laboratory work\n'
    '📝 - Seminar\n'
    '📢 - Lecture\n'
    '❓ - Consultation\n'
)
profile_menu = _('Profile menu')

group_choose = _('Current group: {group_name}\n\n'
                 'Enter a group number or select from your favorites')
group_removed = _('Group removed from favorites!')
group_added = _('Group added to favorites!')
group_changed = _('Current group changed!')
group_already_selected = _('This group is already selected!')
group_not_exist = _('❌ No such group exists!')

in_development = _('Functionality in development')

schedule_day_template = _(
    '               {day_of_week}\n'
    '————————————————\n'
    '{lessons}'
    '————————————————\n\n'
)

lesson_template = _(
    '● {lesson_type} {start_time} - {end_time}  |  {lesson_name}  |  {building} {auditory}'
)

full_schedule_pointer = '➤'

teachers_template = _(
    'List of teachers:\n\n'
    '————————————————\n'
    '{teachers}'
)

teacher = (
    '{lesson_name} [{lesson_types}]\n'
    '{full_name}\n'
    '————————————————\n'
)

kai_error = _('An error occurred on the KAI side. Try later')

select_group = _('Select group')
