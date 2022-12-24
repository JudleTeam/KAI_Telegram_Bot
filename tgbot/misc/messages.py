def _(text):
    """
    Use this function to initialize strings so pybabel can find them
    :param text:
    :return:
    """
    return text


hello = _('Hello, {name}!')
spam_block = _('You have been blocked for spam!')
spam_unblock = _('Unlocked, you can continue to use the bot.')
user_unregistered = _('It looks like you aren\'t registered in the bot. Type "/start" to fix it.')
user_blocked = _('You are blocked in the bot! If this is an error, contact the administrator.')
