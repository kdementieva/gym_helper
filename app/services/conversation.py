from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_message import ConversationMessage
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
)


async def save_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    content: str,
):
    message = ConversationMessage(
        user_id=user_id,
        role=role,
        content=content,
    )

    session.add(message)
    await session.commit()


async def get_recent_messages(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
):
    result = await session.execute(
        select(ConversationMessage)
        .where(
            ConversationMessage.user_id == user_id
        )
        .order_by(
            ConversationMessage.created_at.desc()
        )
        .limit(limit)
    )

    messages = list(result.scalars().all())
    messages.reverse()

    return messages

def to_langchain_messages(messages):
    result = []

    for message in messages:
        if message.role == "user":
            result.append(
                HumanMessage(content=message.content)
            )

        elif message.role == "assistant":
            result.append(
                AIMessage(content=message.content)
            )

    return result