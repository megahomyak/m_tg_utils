from typing import Tuple
import asyncio
import logging
import sys

import aiogram
from .bot import BotHelper


class Base:

    def __init__(self):
        self.bot_helper = bot_helper

    def bot(self):


    def start(self, enable_logging=True):
        if enable_logging:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(self.bot_helper.start())


def create(token: str) -> Tuple[Base, BotHelper, aiogram.Bot]:
    bot = aiogram.Bot(token)
    bot_helper = BotHelper(bot)
    base = Base(bot_helper)
    return (base, bot_helper, bot)
