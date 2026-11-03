from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from test_workspace_routes import context_for

from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import Organization, User
from oligospace_api.schemas.workspace import UserAdminUpdate
from oligospace_api.services.workspace import update_user

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)

COMMIT_DELAY_SECONDS = 0.4


@dataclass
class AdminGroup:
    engine: AsyncEngine
    organization_id: uuid.UUID
    admin_ids: list[uuid.UUID]


async def _new_session(engine: AsyncEngine) -> AsyncSession:
    session = async_sessionmaker(engine, expire_on_commit=False)()
    original_commit = session.commit

    async def delayed_commit() -> None:
        # Hold each transaction open after its writes so the concurrent request overlaps it.
        await asyncio.sleep(COMMIT_DELAY_SECONDS)
        await original_commit()

    session.commit = delayed_commit  # type: ignore[method-assign]
    return session


@pytest.fixture
async def admin_group_factory(integration_database_url: str):  # type: ignore[no-untyped-def]
    engine = create_async_engine(integration_database_url, pool_size=10)

    async def make(admin_count: int) -> AdminGroup:
        unique = uuid.uuid4().hex
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            organization = Organization(
                name=f"Admin concurrency {unique}", slug=f"admin-concurrency-{unique}", active=True
            )
            session.add(organization)
            await session.flush()
            admins = [
                User(
                    oidc_subject=f"admin-{index}-{unique}",
                    email=f"admin-{index}-{unique}@integration.test",
                    display_name=f"Concurrent administrator {index}",
                    active=True,
                    global_role=GlobalRole.ADMIN,
                    organization_id=organization.id,
                )
                for index in range(admin_count)
            ]
            session.add_all(admins)
            await session.commit()
            return AdminGroup(engine, organization.id, [admin.id for admin in admins])

    yield make
    await engine.dispose()


async def _active_admin_count(engine: AsyncEngine, organization_id: uuid.UUID) -> int:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.organization_id == organization_id,
                User.active.is_(True),
                User.global_role == GlobalRole.ADMIN,
            )
        )
        return int(count or 0)


async def _act(
    group: AdminGroup, actor_id: uuid.UUID, target_id: uuid.UUID, change: dict[str, object]
) -> str:
    """Run one admin request in its own session/transaction; return 'ok' or the refusal code."""
    session = await _new_session(group.engine)
    try:
        actor = await session.get(User, actor_id)
        assert actor is not None
        try:
            await update_user(
                session,
                context_for(actor).principal,
                target_id,
                UserAdminUpdate(**change),  # type: ignore[arg-type]
            )
        except HTTPException as error:
            await session.rollback()
            return str(error.detail["code"])
        return "ok"
    finally:
        await session.close()


@pytest.mark.parametrize(
    ("change_a", "change_b"),
    [
        ({"global_role": "member"}, {"global_role": "member"}),
        ({"active": False}, {"active": False}),
        ({"global_role": "viewer"}, {"active": False}),
    ],
)
async def test_two_administrators_cannot_remove_each_other_concurrently(
    admin_group_factory,
    change_a: dict[str, object],
    change_b: dict[str, object],  # type: ignore[no-untyped-def]
) -> None:
    group: AdminGroup = await admin_group_factory(2)
    first, second = group.admin_ids
    # Each administrator removes the other one while both transactions overlap.
    results = await asyncio.gather(
        _act(group, first, second, change_a), _act(group, second, first, change_b)
    )
    assert sorted(results) == ["last_active_administrator_required", "ok"], results
    assert await _active_admin_count(group.engine, group.organization_id) == 1


async def test_concurrent_removal_with_a_third_administrator_keeps_one(
    admin_group_factory,  # type: ignore[no-untyped-def]
) -> None:
    group: AdminGroup = await admin_group_factory(3)
    first, second, third = group.admin_ids
    # Three administrators remove each other in a cycle; the last one standing must remain.
    results = await asyncio.gather(
        _act(group, first, second, {"active": False}),
        _act(group, second, third, {"active": False}),
        _act(group, third, first, {"active": False}),
    )
    assert results.count("ok") == 2, results
    assert results.count("last_active_administrator_required") == 1, results
    assert await _active_admin_count(group.engine, group.organization_id) == 1


async def test_administrators_remain_changeable_when_another_active_one_exists(
    admin_group_factory,  # type: ignore[no-untyped-def]
) -> None:
    group: AdminGroup = await admin_group_factory(2)
    first, second = group.admin_ids
    assert await _act(group, first, second, {"display_name": "Renamed"}) == "ok"
    assert await _act(group, first, second, {"global_role": "member"}) == "ok"
    assert await _act(group, first, second, {"global_role": "admin", "active": True}) == "ok"
    assert await _active_admin_count(group.engine, group.organization_id) == 2
