from aiogram.utils.callback_data import CallbackData

navigation = CallbackData('nav', 'to', 'payload')
language_choose = CallbackData('lang_chs', 'lang_id', 'code')
schedule = CallbackData('schedule', 'action', 'payload')
change_schedule_week = CallbackData('change_week', 'action', 'payload')
