import asyncio
from collections import defaultdict

from aiogram.types import Message


_media_groups: dict[str, list[Message]] = defaultdict(list)
_media_group_tasks: dict[str, asyncio.Task] = {}


async def collect_media_group(
    message: Message,
    callback,
    delay: float = 1.0,
):
    media_group_id = message.media_group_id

    _media_groups[media_group_id].append(message)

    old_task = _media_group_tasks.get(media_group_id)

    if old_task:
        old_task.cancel()

    async def process():
        try:
            await asyncio.sleep(delay)

            messages = _media_groups.pop(
                media_group_id,
                [],
            )

            _media_group_tasks.pop(
                media_group_id,
                None,
            )

            messages.sort(
                key=lambda item: item.message_id
            )

            await callback(messages)

        except asyncio.CancelledError:
            pass

    _media_group_tasks[media_group_id] = (
        asyncio.create_task(process())
    )