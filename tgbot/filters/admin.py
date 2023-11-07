from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.config import Config


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message, config: Config) -> Union[bool, Dict[str, Any]]:
        return message.from_user.id in config.bot.admin_ids
