from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: str | None,
    first_name: str,
    language_code: str | None,
) -> User:

    result = await session.execute(
        select(User).where(User.telegram_id == tg_id)
    )

    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(
        telegram_id=tg_id,
        username=username,
        first_name=first_name,
        language_code=language_code,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user

async def set_preferred_language(
    session,
    user,
    language: str,
):
    user.preferred_language = language

    await session.commit()
    await session.refresh(user)

    return user