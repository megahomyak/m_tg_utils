from typing import List
from aiogram import Bot as AiogramBot
from aiogram import Dispatcher
from aiogram.types import Document, Message
import asyncio
import logging
import sys
from dataclasses import dataclass
import itertools


@dataclass
class MessageUpdate:
    message: Message
    media: List[Document]


class MessageOrganizer:

    def __init__(self) -> None:
        self.ungrouped = []
        self.grouped = {}

    def add(self, message: Message):
        if message.media_group_id is None:
            if message.document is None:
                media = []
            else:
                media = [message.document]
            self.ungrouped.append(MessageUpdate(message, media))
        else:
            self.grouped.setdefault(message.media_group_id, MessageUpdate(message, [])).media.append(message.document)


class Bot(AiogramBot):

    def __init__(self, token: str):
        super().__init__(token=token)
        self.dp = Dispatcher()
        self._update_offset = None
        self._message_handler = None
        self._callback_query_handler = None

    def start(self, enable_logging=True):
        async def start():
            updates = await self.get_updates(offset=self._update_offset)
            if updates:
                self._update_offset = max(updates, key=lambda update: update.update_id).update_id + 1
                organizer = MessageOrganizer()
                for update in updates:
                    if update.message is not None:
                        organizer.add(update.message)
                    elif update.callback_query is not None:
                        if self._callback_query_handler is not None:
                            asyncio.create_task(self._callback_query_handler(update.callback_query))
                if self._message_handler is not None:
                    for message in itertools.chain(organizer.ungrouped, organizer.grouped.values()):
                        asyncio.create_task(self._message_handler(message))
        if enable_logging:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(start())

    def message_handler(self, function):
        self._message_handler = function

    def callback_query_handler(self, function):
        self._callback_query_handler = function
