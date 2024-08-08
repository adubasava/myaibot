import asyncio
from config import settings
from aiogram import Bot, Dispatcher
from handlers import router
from aiogram.types import BotCommand


bot = Bot(token = settings.telegram_bot_api_token)
dp = Dispatcher()

async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start',
                   description='Начало работы')
    ]
    await bot.set_my_commands(main_menu_commands)

async def main():   
    dp.startup.register(set_main_menu) 
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')