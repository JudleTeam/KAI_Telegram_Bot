from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ErrorEvent

router = Router()


@router.error(ExceptionTypeFilter(TelegramBadRequest))
async def handle_error(event: ErrorEvent):
    pass
