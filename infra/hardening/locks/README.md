# Dependency lock provenance

These locks preserve installed runtime closures exported from baseline source
`9ebbf2cd993395af2b154efb0b4cf5a76b4dd079`, using Python 3.12.8. Existing
requirements files and `provenance.json` have not been regenerated or changed by
the reusable tooling addition. Kombu remains 5.6.2.

`inputs/*-dependencies.json` preserves the original three export receipts
byte-for-byte. Those receipts lack root versions and architecture; do not infer
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

```sh
python3.12 -m unittest discover -s infra/hardening/tests -p test_dependency_locks.py
```

Tests check direct runtime pins/extras against pyprojects, transitive versions
against preserved exports, exact release URLs/hash syntax, explicit build-root
inclusion, marker/extras traversal and offline byte-for-byte lock reproduction.
