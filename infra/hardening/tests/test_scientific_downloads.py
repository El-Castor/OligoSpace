import hashlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


spec = importlib.util.spec_from_file_location(
    "scientific_downloads", Path(__file__).parents[1] / "scientific_downloads.py"
)
module = importlib.util.module_from_spec(spec)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        spec.loader.exec_module(module)

    def test_stream_reports_exact_bytes_and_locally_observed_hashes(self):
        data = b"synthetic-public-archive" * 100
        expected = hashlib.md5(data).hexdigest()
        result = module.hash_stream(
            io.BytesIO(data), expected, limit=len(data), chunk_size=7
        )
        self.assertEqual(
            result,
            {
                "bytes": len(data),
                "md5": expected,
                "sha256": hashlib.sha256(data).hexdigest(),
            },
        )
        response = io.BytesIO(data)
        response.geturl = lambda: module.ARCHIVES["arm64"]["url"]
        response.headers = {}
        with (
            patch.object(module, "open_archive", return_value=response),
            patch.dict(module.ARCHIVES["arm64"], {"md5": expected}),
        ):
            report = module.observe("arm64")
        self.assertEqual(
            report["sha256_authority"], "locally_observed_not_upstream_signed"
        )
        self.assertNotIn("synthetic", str(report))

    def test_wrong_md5_and_oversize_are_fixed_failures(self):
        for stream, expected, limit, reason in (
            (io.BytesIO(b"data"), "0" * 32, 100, "BLAST_MD5_MISMATCH"),
            (
                io.BytesIO(b"data"),
                hashlib.md5(b"data").hexdigest(),
                3,
                "BLAST_SIZE_LIMIT",
            ),
        ):
            with (
                self.subTest(reason=reason),
                self.assertRaises(module.DownloadFailure) as error,
            ):
                module.hash_stream(stream, expected, limit=limit, chunk_size=2)
            self.assertEqual(str(error.exception), reason)

    def test_redirect_guard_rejects_cross_origin_and_credentials(self):
        handler = module.SameOriginRedirect()
        from urllib.request import Request

        request = Request(module.ARCHIVES["amd64"]["url"])
        for url in (
            "http://ftp.ncbi.nlm.nih.gov/a",
            "https://evil.example/a",
            "https://user:secret@ftp.ncbi.nlm.nih.gov/a",
            "https://ftp.ncbi.nlm.nih.gov/a?token=private",
        ):
            with self.subTest(url=url), self.assertRaises(module.DownloadFailure):
                handler.redirect_request(request, None, 302, "", {}, url)
        accepted = handler.redirect_request(
            request, None, 302, "", {}, "https://ftp.ncbi.nlm.nih.gov/blast/redirected"
        )
        self.assertEqual(
            accepted.full_url, "https://ftp.ncbi.nlm.nih.gov/blast/redirected"
        )

    def test_network_exception_is_not_exposed(self):
        with patch.object(
            module,
            "open_archive",
            side_effect=HTTPError("private-url", 403, "private-error", {}, None),
        ):
            with self.assertRaises(module.DownloadFailure) as error:
                module.observe("amd64")
        self.assertEqual(str(error.exception), "BLAST_DOWNLOAD_FAILED")

    def test_oversize_header_and_overall_deadline_abort_without_retention(self):
        response = io.BytesIO(b"not consumed")
        response.geturl = lambda: module.ARCHIVES["amd64"]["url"]
        response.headers = {"Content-Length": str(module.MAX_BYTES + 1)}
        with patch.object(module, "open_archive", return_value=response):
            with self.assertRaises(module.DownloadFailure) as error:
                module.observe("amd64")
        self.assertEqual(str(error.exception), "BLAST_SIZE_LIMIT")
        with patch.object(
            module.time, "monotonic", side_effect=[0, module.TOTAL_TIMEOUT + 1]
        ):
            with self.assertRaises(module.DownloadFailure) as error:
                module.hash_stream(io.BytesIO(b"data"), "0" * 32)
        self.assertEqual(str(error.exception), "BLAST_DOWNLOAD_TIMEOUT")


if __name__ == "__main__":
    unittest.main()
