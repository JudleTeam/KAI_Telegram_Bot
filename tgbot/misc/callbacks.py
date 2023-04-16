from aiogram.utils.callback_data import CallbackData


navigation = CallbackData('nav', 'to', 'payload')
action = CallbackData('act', 'name', 'payload')
language_choose = CallbackData('lang_chs', 'lang_id', 'code', 'payload')
schedule = CallbackData('schedule', 'action', 'payload')
change_schedule_week = CallbackData('change_week', 'action', 'payload')
group_choose = CallbackData('grp_chs', 'id', 'action', 'payload')  # actions - 'select', 'add', 'remove'
cancel = CallbackData('cancel', 'to', 'payload')
