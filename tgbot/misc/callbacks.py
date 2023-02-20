from aiogram.utils.callback_data import CallbackData

navigation = CallbackData('nav', 'to', 'payload')
language_choose = CallbackData('lang_chs', 'lang_id', 'code')
group_choose = CallbackData('grp_chs', 'id', 'action')  # actions - 'select', 'add', 'remove'
