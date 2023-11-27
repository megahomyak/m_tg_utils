from aiogram import Bot as AiogramBot
from aiogram import Dispatcher
import asyncio
import logging
import sys

class Bot(AiogramBot):

    def __init__(self, token: str):
        super().__init__(token=token)
        self.dp = Dispatcher()

    def start(self, enable_logging=True):
        async def start():
            await self.dp.start_polling(self)
        if enable_logging:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(start())
