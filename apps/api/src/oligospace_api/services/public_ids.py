from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.models.registry import PublicIdCounter


async def allocate_public_id(session: AsyncSession, prefix: str) -> str:
    statement = (
        insert(PublicIdCounter)
        .values(prefix=prefix, last_value=1)
        .on_conflict_do_update(
            index_elements=[PublicIdCounter.prefix],
            set_={"last_value": PublicIdCounter.last_value + 1},
        )
        .returning(PublicIdCounter.last_value)
    )
    value = int(await session.scalar(statement))
    return f"{prefix}-{value:06d}"
