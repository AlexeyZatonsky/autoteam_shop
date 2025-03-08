import uvicorn
import asyncio
from .bot.bot import AutoteamBot
from .settings.config import settings


async def main():
    # Создаем и запускаем бота
    bot = AutoteamBot()
    
    # Запускаем FastAPI приложение и бота
    server = uvicorn.Server(
        config=uvicorn.Config(
            'src.app:app',
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            reload=True
        )
    )

    # Запускаем оба компонента асинхронно
    await asyncio.gather(
        server.serve(),
        bot.start()
    )


if __name__ == '__main__':
    asyncio.run(main())