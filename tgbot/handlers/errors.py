from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.exceptions import CallbackAnswerException

router = Router()


@router.error(ExceptionTypeFilter(CallbackAnswerException))
async def handle_error(update, error):
    pass
