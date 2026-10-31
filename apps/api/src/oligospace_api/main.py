import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from oligospace_api import __version__
from oligospace_api.api.router import api_router
from oligospace_api.core.audit import REQUEST_ID_PATTERN, request_id_context
from oligospace_api.core.config import get_settings
from oligospace_api.core.logging import configure_logging
from oligospace_api.services.sequence_analysis import InvalidSequenceError

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    yield


app = FastAPI(
    title="OligoSpace API",
    version=__version__,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
)


@app.middleware("http")
async def correlate_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())
    token = request_id_context.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(token)


@app.exception_handler(InvalidSequenceError)
async def invalid_sequence_handler(_: Request, exc: InvalidSequenceError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "invalid_sequence",
                "message": str(exc),
                "invalid_symbols": sorted(exc.invalid_symbols),
            }
        },
    )


app.include_router(api_router, prefix="/api/v1")
