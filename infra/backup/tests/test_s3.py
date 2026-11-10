import io
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s3 import export_buckets, restore_buckets, validate_export


class FakeS3:
    def __init__(self):
        self.objects = {"bucket": {"quarantine/é #?.bin": b"abc"}}

    def get_bucket_versioning(self, b):
        return SimpleNamespace(status=None)

    def list_objects(self, b, recursive=True):
        return [
            SimpleNamespace(object_name=k, etag="etag", size=len(v))
            for k, v in self.objects.get(b, {}).items()
        ]

    def stat_object(self, b, k):
        return SimpleNamespace(
            size=len(self.objects[b][k]),
            content_type="text/plain",
            metadata={"X-Amz-Meta-kind": "quarantine"},
            etag="etag",
        )

    def get_object(self, b, k):
        r = io.BytesIO(self.objects[b][k])
        r.release_conn = lambda: None
        return r

    def get_object_tags(self, b, k):
        return {"classification": "synthetic"}

    def bucket_exists(self, b):
        return b in self.objects

    def make_bucket(self, b):
        self.objects[b] = {}

    def put_object(self, b, k, data, length, **kwargs):
        self.objects[b][k] = data.read()

    def set_object_tags(self, *args):
        pass


class S3Tests(unittest.TestCase):
    def test_missing_object_fails_before_target_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = FakeS3()
            data = export_buckets(src, ["bucket"], root)
            (root / data[0]["objects"][0]["file"]).unlink()
            target = FakeS3()
            target.objects = {}
            with self.assertRaises(ValueError):
                restore_buckets(target, data, root)
            self.assertEqual(target.objects, {})

    def test_roundtrip_and_nonempty_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = FakeS3()
            data = export_buckets(src, ["bucket"], root)
            validate_export(data, root)
            target = FakeS3()
            target.objects = {}
            restore_buckets(target, data, root)
            self.assertEqual(target.objects, src.objects)
            with self.assertRaises(ValueError):
                restore_buckets(target, data, root)

    def test_versioned_bucket_refused(self):
        src = FakeS3()
        src.get_bucket_versioning = lambda b: SimpleNamespace(status="Enabled")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                export_buckets(src, ["bucket"], Path(d))
