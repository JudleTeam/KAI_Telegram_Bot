import asyncio
import logging
from os import environ

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


async def main():
    load_dotenv(dotenv_path='stub/.env')
    bot = Bot(token=environ.get('BOT_TOKEN'), parse_mode='HTML')
    dp = Dispatcher()

    stub_text = (
        'Telegram-бот пока не поддерживается.\n\n'
        'Возможно, когда-нибудь, он снова заработает и станет ещё лучше.\n\n'
        'А может быть появится что-то покруче бота...\n\n'
        'Если будут новости, они придут в этот чат, так что не спеши блокировать бота ;)'
    )

    @dp.message()
    async def handle_all_messages(message: types.Message):
        await message.answer(text=stub_text)

    @dp.callback_query()
    async def handle_all_callback_queries(callback_query: types.CallbackQuery):
        await callback_query.message.answer(text=stub_text)
        await callback_query.answer()

    logger.info('Starting bot')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error('Bot stopped!')
        raise e
