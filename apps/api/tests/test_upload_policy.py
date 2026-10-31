from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, UploadFile

from oligospace_api.api.routes.laboratory import upload_attachment
from oligospace_api.core.config import Settings


@pytest.mark.parametrize("environment", ["development", "test", "production"])
async def test_disabled_upload_does_not_read_or_store(environment: str) -> None:
    file = AsyncMock(spec=UploadFile)
    storage = AsyncMock()
    session = AsyncMock()
    with pytest.raises(HTTPException) as error:
        await upload_attachment(
            "run",
            "RUN-HIDDEN",
            file,
            AsyncMock(),
            session,
            storage,
            Settings(environment=environment),
        )
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "uploads_disabled"
    file.read.assert_not_called()
    storage.put.assert_not_called()
    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_production_uploads_fail_closed_even_with_opt_in() -> None:
    assert not Settings(environment="production", uploads_enabled=True).uploads_allowed
    assert Settings(environment="test", uploads_enabled=True).uploads_allowed
