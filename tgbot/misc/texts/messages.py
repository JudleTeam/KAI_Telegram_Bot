from tgbot.misc.texts import _

welcome = _('Welcome to KAI bot! Tap button below to choose your language')
main_menu = _('Main menu')

language_changed = _('Language changed')

spam_block = _('You have been blocked for spam')
spam_unblock = _('Unlocked, you can continue to use the bot')

user_unregistered = _('It looks like you aren\'t registered in the bot. Type "/start" to fix it')
user_blocked = _('You are blocked in the bot! If this is an error, contact the administrator')

language_not_available = _('The language you are using is no longer available. '
                           'Contact the administrator or change the language')
language_choose = _('Please select your language')

schedule_menu = _(
    'Schedule menu\n'
    'Now {week} week\n\n'
    '🧪 - Laboratory work\n'
    '📝 - Seminar\n'
    '📢 - Lecture\n'
    '❓ - Consultation\n'
)
profile_menu = _(
    'Profile menu\n\n'
    'Selected group: {s_group_name}\n'
    'Your roles: {roles}'
    )

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
    'List of teachers {group_name}:\n\n'
    '————————————————\n'
    '{teachers}'
)

teacher = (
    '{lesson_name} [{lesson_types}]\n'
    '{full_name}\n'
    '————————————————\n'
)

kai_error = _('An error occurred on the KAI side. Please, try later')
base_error = _('Something went wrong')

select_group = _('Select group')

ban_unban_bad_format = _(
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
share_contact = _('Please, share your contact')
phone_verified = _('✅ Your phone number has been verified!')
phone_found = _('☑️ Your phone number was found in the database and your profile is now verified')
phone_not_found = _('❌ Your phone number was not found in the database')
credentials_busy = _('❌ Someone is already signed in with these credentials')
account_unlinked = _('You have successfully unlinked your account')
channel_advertising = _('Subscribe to the Telegram channel of the project! '
                        'There will be the latest news on the project and more!')
kai_account_busy = _('❌ Account with this number already linked to someone else Telegram')
dont_do = _('You don\'t have to do this!')
group_chat_error = _('Sorry, I don\'t know how to work in group chats yet')

education_menu = _('Education menu')
my_group_menu = _(
    'My group ({group_name})\n\n'
    
    'Year: {year} | Faculty: {faculty}\n'
    'Institute: {institute}\n'
    'Departament: {departament}\n'
    'Speciality: {speciality}\n'
    'Profile: {profile}\n\n'
    
    'Pinned text:\n{pinned_text}'
)
need_be_verified = _('You need to be verified to access')
missing = _('Missing')
classmates_list = _(
    'My group ({group_name})\n\n'
    'Classmates:\n{classmates}'
)

set_prefix_bad_format = _(
    'Invalid /set_prefix command format. The command should be followed by the user\'s Telegram ID, '
    'then a new prefix (can be empty, limit 32 symbols). Example: "/set_prefix 393867797 💩"'
)
set_prefix_bad_user = _('User {user_id} does not exist or is not verified')
prefix_set = _('User {user_id} was prefixed with {prefix}')

send_message_bad_format = _(
    'Invalid /send_message command format. The command must be a reply to a message that you must send. '
    'The command should be followed by the user\'s Telegram ID, to whom the message will be sent'
)
message_sent = _('The message was sent to user {user_id}')

verified_info = _(
    'Full name: {full_name}\n'
    'Position in the group: {group_pos}\n'
    'Native group: {n_group_name}\n'
    'Phone: {phone}\n'
    'Email: {email}'
)
authorized_info = _(
    'Birthday: {birthday}\n'
    'Number of the record book: {zach}'
)
for_admin_info = _(
    'Telegram ID: {telegram_id}\n'
    'Telegram full name: {tg_full_name}\n'
    'Telegram mention: {tg_mention}\n'
    'Telegram phone: {telegram_phone}\n'
    'Is blocked: {is_blocked}\n'
    'Selected group: {s_group_name}\n'
    'Roles: {roles}'
)

pin_text_input = _('Enter the text of the pinned message')
documents = _('Documents')

help_menu = _('Help menu')
