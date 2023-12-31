from dataclasses import dataclass
from typing import List, Optional, Sequence, Union
import aiogram
from aiogram.types import InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo, Message, MessageEntity
import asyncio
import itertools
import textwrap


SendableAttachment = Union[InputMediaAudio, InputMediaVideo, InputMediaPhoto, InputMediaDocument]


def _input_media_from_message(message: Message) -> Optional[SendableAttachment]:
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


def _repack(attachments: Sequence[SendableAttachment], text, entities):
    first, *rest = attachments
    repacked_first = type(first)(media=first.media, caption=text, caption_entities=entities)
    attachments = [repacked_first] + rest
    return attachments


_CAPTION_LENGTH_LIMIT = 1024
_REGULAR_MESSAGE_TEXT_LENGTH_LIMIT = 4096


class Bot:

    def __init__(self, token: str):
        self.inner = aiogram.Bot(token)
        self._update_offset = None
        self._message_handler = None
        self._callback_query_handler = None

    async def start(self):
        while True:
            updates = await self.inner.get_updates(offset=self._update_offset, timeout=20)
            if updates:
                self._update_offset = max(updates, key=lambda update: update.update_id).update_id + 1
                message_organizer = _MessageOrganizer()
                for update in updates:
                    if update.message is not None:
                        message_organizer.add(update.message)
                    elif update.callback_query is not None:
                        if self._callback_query_handler is not None:
                            asyncio.create_task(self._callback_query_handler(update.callback_query))
                if self._message_handler is not None:
                    for message in message_organizer:
                        asyncio.create_task(self._message_handler(message))

    def message_handler(self, function):
        self._message_handler = function

    def callback_query_handler(self, function):
        self._callback_query_handler = function

    async def send_message(self, chat_id, text, attachments: Sequence[SendableAttachment] = (), entities=None, *args, **kwargs):
        if len(attachments) == 0:
            entities: MessageEntity
            text_parts = textwrap.wrap(text, _CAPTION_LENGTH_LIMIT) or [""]
            for part in text_parts:
                await self.inner.send_message(
                    chat_id, part, *args, entities=entities, **kwargs,
                )
        else:
            text_parts = textwrap.wrap(text, _REGULAR_MESSAGE_TEXT_LENGTH_LIMIT) or [""]
            *beginning, last = text_parts
            for part in beginning:
                await self.inner.send_message(
                    chat_id, part, *args, entities=entities, **kwargs,
                )
            await self.inner.send_media_group(
                chat_id, media=_repack(attachments, last, entities), *args, **kwargs,
            )


@dataclass
class NewMessageContext:
    message: Message
    attachment_messages: List[Message]

    def input_media(self):
        media = []
        for message in itertools.chain((self.message,), self.attachment_messages):
            media_piece = _input_media_from_message(message)
            if media_piece is not None:
                media.append(media_piece)
        return media

    @property
    def text(self):
        return self.message.text or self.message.caption

    @property
    def formatting_entities(self):
        return self.message.entities or self.message.caption_entities


class _MessageOrganizer:

    def __init__(self) -> None:
        self.ungrouped = []
        self.grouped = {}

    def add(self, message: Message):
        if message.media_group_id is None:
            self.ungrouped.append(NewMessageContext(message, []))
        else:
            try:
                self.grouped[message.media_group_id].attachment_messages.append(message)
            except KeyError:
                self.grouped[message.media_group_id] = NewMessageContext(message, [])

    def __iter__(self):
        return itertools.chain(self.ungrouped, self.grouped.values())
