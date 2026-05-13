"""User repository for database operations."""

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def upsert_user(
    session: AsyncSession,
    clerk_id: str,
    email: str,
) -> User:
    """
    Upsert a user - insert or update if exists.
    Uses PostgreSQL UPSERT for atomicity.

    Args:
        session: Database session
        clerk_id: Clerk user ID
        email: User's email address

    Returns:
        The created or updated User
    """
    stmt = insert(User).values(clerk_id=clerk_id, email=email)

    stmt = stmt.on_conflict_do_update(
        index_elements=["clerk_id"],
        set_={
            "email": email,
            "updated_at": func.now(),
        },
    ).returning(User)

    result = await session.execute(stmt)
    user = result.scalar_one()
    await session.commit()

    return user


async def get_by_clerk_id(
    session: AsyncSession,
    clerk_id: str,
) -> Optional[User]:
    """
    Get a user by their Clerk ID.

    Args:
        session: Database session
        clerk_id: Clerk user ID

    Returns:
        User or None if not found
    """
    stmt = select(User).where(User.clerk_id == clerk_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
