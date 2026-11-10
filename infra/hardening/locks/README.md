# Dependency lock provenance

These locks derive from installed runtime closures exported from baseline source
`9ebbf2cd993395af2b154efb0b4cf5a76b4dd079`, using Python 3.12.8. The current API
graph includes two explicit security updates: PyJWT crypto 2.14.0 → 2.15.0 for
CVE-2026-101918/CVE-2026-102275, and python-multipart 0.0.30 → 0.0.31 for
CVE-2026-53540. These are fixes indicated by the candidate scan and authorized
for targeted remediation; this metadata does not prove their runtime remediation.
The worker additionally updates only Biopython 1.85 → 1.88 for maintainer
[GHSA-cxcq-r753-xf25](https://github.com/biopython/biopython/security/advisories/GHSA-cxcq-r753-xf25)
(HIGH, Bio.Nexus eval, fixed in 1.88) and CVE-2025-68463 (XXE, fixed upstream
in 1.87). The maintainer advisory is not covered by the observed Trivy result;
absence from a scanner database is not absence of a vulnerability. PyPI 1.88
declares `numpy` without a version bound; its requirement accepts the unchanged
locked NumPy 2.5.4. No other worker version changes. Kombu remains 5.6.2.

`inputs/baseline-api-dependencies.json` preserves the original API export
byte-for-byte; `baseline/api.txt` and `baseline/provenance.json` preserve its
original lock and complete original release metadata. The current
`inputs/api-dependencies.json` is explicitly derived, retaining the original
Python observation while recording its baseline SHA256 and the two approved
changes. It is not a newly observed installed closure. Worker originals are
retained separately as well: `inputs/baseline-worker-dependencies.json`
and `baseline/worker.txt` preserve the original worker graph/lock, while the current
worker input explicitly records its baseline hash, approved Biopython update and
NumPy requirement check. The build input remains the original export. Original
receipts lack root versions and architecture; do not infer
architecture or universal marker coverage. The original build export excludes its
root: generation intentionally adds `hatchling==1.27.0`, the explicit requirement
in both pyprojects. New exports also record the installed root version.

## Export inside the exact baseline environment

Make `freeze_dependencies.py` available read-only inside the disposable baseline
image and run its installed interpreter, choosing the applicable root:

```sh
python /qualification/freeze_dependencies.py export \
  --root oligospace-api --output /evidence/api-dependencies.json
python /qualification/freeze_dependencies.py export \
  --root oligospace-bioinfo --output /evidence/worker-dependencies.json
python /qualification/freeze_dependencies.py export \
  --root hatchling --output /evidence/build-dependencies.json
```

Use the worker environment for its export. Export follows installed metadata and
`packaging` markers, preserving requested extras such as Celery Redis, JWT crypto
and Psycopg binary and excluding unrequested development extras. It rejects
installed versions that violate declared requirements. Markers reflect only that
interpreter/platform; another platform may need a separately reviewed closure.
No package is installed or upgraded.

## Reproduce existing locks offline

Run from the repository root with a new empty output directory:

```sh
python3.12 infra/hardening/freeze_dependencies.py generate \
  --api-graph infra/hardening/locks/inputs/api-dependencies.json \
  --worker-graph infra/hardening/locks/inputs/worker-dependencies.json \
  --build-graph infra/hardening/locks/inputs/build-dependencies.json \
  --build-root-version 1.27.0 \
  --release-provenance infra/hardening/locks/provenance.json \
  --output /tmp/oligospace-lock-reproduction
```

Requirements files reproduce byte-for-byte; new provenance additionally records
input-graph SHA256s. Generation refuses nonempty output directories, mismatched
root versions, duplicate names, invalid identities/hashes and Kombu version drift.

Omitting `--release-provenance` selects online lookup of only exact version URLs:
`https://pypi.org/pypi/{name}/{version}/json`. It validates the returned version,
rejects redirects and records response and release-artifact SHA256s. It never
resolves latest versions or executes downloads. PyPI may add/remove artifacts,
changing hash sets without changing versions: review differences before adoption.

Existing response hashes document metadata originally observed; raw responses
are not retained, and authenticity cannot be re-established offline by syntax
checks. Locks retain all observed distribution hashes, not a target wheel choice.
Successful `pip --require-hashes` installation, supported wheels and native
runtime/scientific checks remain separate evidence. Python locks do not freeze
apt, Conda, toolchains or external scientific executables.

## Offline verification

The security updates require fresh native candidate scans and full OIDC/runtime
qualification. Their presence in a derived graph does not adopt a production
image or establish that all findings are resolved.

```sh
python3.12 -m unittest discover -s infra/hardening/tests -p test_dependency_locks.py
```

Tests check direct runtime pins/extras against pyprojects, transitive versions
against preserved exports, exact release URLs/hash syntax, explicit build-root
inclusion, marker/extras traversal and offline byte-for-byte lock reproduction.
