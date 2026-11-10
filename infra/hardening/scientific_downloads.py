"""Observe fixed official BLAST archives without storing or executing binaries."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERSION = "2.17.0"
BASE = "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.17.0/"
ARCHIVES = {
    "arm64": {
        "url": BASE + "ncbi-blast-2.17.0+-aarch64-linux.tar.gz",
        "md5": "5f9d49b999346e0ddb6637b71af4b22a",
    },
    "amd64": {
        "url": BASE + "ncbi-blast-2.17.0+-x64-linux.tar.gz",
        "md5": "bdec166721de3b55f90a3badc83538e8",
    },
}
MAX_BYTES = 1024 * 1024 * 1024
SOCKET_TIMEOUT = 60
TOTAL_TIMEOUT = 900


class DownloadFailure(ValueError):
    """Only fixed public reason codes may cross the CLI boundary."""


def allowed_url(url):
    try:
        parts = urlsplit(url)
        return (
            parts.scheme == "https"
            and parts.hostname == "ftp.ncbi.nlm.nih.gov"
            and parts.port in (None, 443)
            and not parts.username
            and not parts.password
            and not parts.query
            and not parts.fragment
        )
    except (TypeError, ValueError):
        return False


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(req.full_url) or not allowed_url(newurl):
            raise DownloadFailure("BLAST_REDIRECT_REFUSED")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_archive(url):
    # urllib's default HTTPSHandler verifies certificates and hostname using
    # system trust. No custom SSL context or unverified transport is installed.
    return build_opener(SameOriginRedirect()).open(
        Request(url, headers={"User-Agent": "OligoSpace-BLAST-provenance/1"}),
        timeout=SOCKET_TIMEOUT,
    )


def hash_stream(stream, expected_md5, *, limit=MAX_BYTES, chunk_size=1024 * 1024):
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    size = 0
    deadline = time.monotonic() + TOTAL_TIMEOUT
    while True:
        if time.monotonic() > deadline:
            raise DownloadFailure("BLAST_DOWNLOAD_TIMEOUT")
        chunk = stream.read(min(chunk_size, limit - size + 1))
        if time.monotonic() > deadline:
            raise DownloadFailure("BLAST_DOWNLOAD_TIMEOUT")
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise DownloadFailure("BLAST_SIZE_LIMIT")
        md5.update(chunk)
        sha256.update(chunk)
    if md5.hexdigest() != expected_md5:
        raise DownloadFailure("BLAST_MD5_MISMATCH")
    return {"bytes": size, "md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def observe(architecture):
    archive = ARCHIVES[architecture]
    try:
        with open_archive(archive["url"]) as response:
            if not allowed_url(response.geturl()):
                raise DownloadFailure("BLAST_REDIRECT_REFUSED")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
                raise DownloadFailure("BLAST_SIZE_LIMIT")
            hashes = hash_stream(response, archive["md5"])
        return {
            "url": archive["url"],
            "version": VERSION,
            "architecture": architecture,
            **hashes,
            "sha256_authority": "locally_observed_not_upstream_signed",
        }
    except DownloadFailure:
        raise
    except Exception:
        # Network/SSL/server errors may embed URLs, headers or local trust paths.
        raise DownloadFailure("BLAST_DOWNLOAD_FAILED") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--architecture", required=True, choices=ARCHIVES)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    success = False
    try:
        report = observe(args.architecture)
        success = True
    except DownloadFailure as error:
        report = {"rule_id": str(error)}
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    except OSError:
        print("BLAST_EVIDENCE_WRITE_FAILED", file=sys.stderr)
        raise SystemExit(1) from None
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
