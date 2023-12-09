import asyncio
import logging
import sys

from .bot import Bot


class Base:

    def __init__(self):
        self._bot = None

    def bot(self, token: str):
        self._bot = Bot(token)
        return self._bot

    def start(self, enable_logging=True):
        if enable_logging:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        if self._bot is not None:
            asyncio.run(self._bot.start())
