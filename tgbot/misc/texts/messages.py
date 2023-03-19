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

kai_error = _('An error occurred on the KAI side. Please, try later')

select_group = _('Select group')

ban_unban_invalid_format = _(
    'Invalid {command} command format. After the command, there should be a user\'s Telegram ID. '
    'Example: "{command} 393867797"'
)

user_not_exist = _('User {user_id} does not exist')
user_has_been_blocked = _('User {user_id} has been blocked')
user_has_been_unblocked = _('User {user_id} has been unblocked')

admin_block = _('You have been blocked by the administrator!')
admin_unblock = _('You have been unblocked by the administrator!')

verification_menu = _(
    'Verification\n\n'
    'Phone verified: {phone_status}\n'
    'KAI credentials: {kai_status}\n'
    'Profile verified: {profile_status}'
)

login_input = _(
    'Verification\n\n'
    'Please, input your login'
)

password_input = _(
    'Verification\n\n'
    'Please, input your password'
)

authorization_process = _('Authorization...\nPlease wait a moment')

bad_credentials = _(
    '‼️ Something went wrong!\n'
    'Looks like you entered the wrong credentials'
)

success_login = _(
    '✅ Hooray!\n'
    'You have successfully verified your account'
)

kai_logout = _('Your credentials have been removed from the database')
