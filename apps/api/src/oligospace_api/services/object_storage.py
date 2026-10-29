from __future__ import annotations

from io import BytesIO

from anyio import to_thread
from minio import Minio

from oligospace_api.core.config import Settings, get_settings


class ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.object_storage_bucket
        self.client = Minio(
            settings.object_storage_endpoint,
            access_key=settings.object_storage_access_key,
            secret_key=settings.object_storage_secret_key,
            secure=settings.object_storage_secure,
        )

    async def put(self, object_key: str, body: bytes, content_type: str) -> None:
        def upload() -> None:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            self.client.put_object(
                self.bucket,
                object_key,
                BytesIO(body),
                len(body),
                content_type=content_type,
            )

        await to_thread.run_sync(upload)


def get_object_storage() -> ObjectStorage:
    return ObjectStorage(get_settings())
