from typing import TYPE_CHECKING, List, Optional, Union
from aiogram import Bot as AiogramBot
from aiogram.types import InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo, Message
import asyncio
import logging
import sys
import itertools


SendableAttachment = Union[InputMediaAudio, InputMediaVideo, InputMediaPhoto, InputMediaDocument]


if TYPE_CHECKING:
    class MessageWithAttachments(Message):
        attachments: List[SendableAttachment]
else:
    class MessageWithAttachments:
        def __init__(self, inner_message, attachments):
            object.__setattr__(self, "_inner_message", inner_message)
            object.__setattr__(self, "_attachments", attachments)

        def __getattribute__(self, name):
            if name == "attachments":
                return object.__getattribute__(self, "_attachments")
            inner_message = object.__getattribute__(self, "_inner_message")
            if name == "text":
                return inner_message.text or inner_message.caption
            return getattr(inner_message, name)

        def __setattr__(self, name, value):
            setattr(object.__getattribute__(self, "_inner_message"), name, value)


class _MessageOrganizer:

    def __init__(self) -> None:
        self.ungrouped = []
        self.grouped = {}

    def add(self, message: Message, file: Optional[SendableAttachment]):
        if message.media_group_id is None:
            if file is None:
                files = []
            else:
                files = [file]
            self.ungrouped.append(MessageWithAttachments(message, files))
        else:
            self.grouped.setdefault(message.media_group_id, MessageWithAttachments(message, [])).attachments.append(file)


def _get_sendable_attachment(message: Message) -> Optional[SendableAttachment]:
    if message.photo is not None:
        biggest_photo = max(message.photo, key=lambda photo: photo.width * photo.height)
        return InputMediaPhoto(media=biggest_photo.file_id)
    if message.document is not None:
        return InputMediaDocument(media=message.document.file_id)
    if message.video is not None:
        return InputMediaVideo(media=message.video.file_id)
    if message.audio is not None:
        return InputMediaAudio(media=message.audio.file_id)
    return None


class Bot(AiogramBot):

    def __init__(self, token: str):
        super().__init__(token=token)
        self._update_offset = None
        self._message_handler = None
        self._callback_query_handler = None

    def start(self, enable_logging=True):
        async def start():
            while True:
                updates = await self.get_updates(offset=self._update_offset, timeout=20)
                if updates:
                    self._update_offset = max(updates, key=lambda update: update.update_id).update_id + 1
                    organizer = _MessageOrganizer()
                    for update in updates:
                        if update.message is not None:
                            organizer.add(update.message, _get_sendable_attachment(update.message))
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


def caption(input_media: List[SendableAttachment], caption, caption_entities=None) -> List[SendableAttachment]:
    first, *rest = input_media
    repacked = type(first)(media=first.media, caption=caption, caption_entities=caption_entities)
    return [repacked] + rest
