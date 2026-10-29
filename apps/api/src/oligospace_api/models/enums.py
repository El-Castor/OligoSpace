from enum import StrEnum
from typing import TypeVar

from sqlalchemy import Enum

EnumType = TypeVar("EnumType", bound=StrEnum)


def database_enum(enum_class: type[EnumType], name: str) -> Enum:
    return Enum(
        enum_class,
        name=name,
        values_callable=lambda members: [member.value for member in members],
    )


class GlobalRole(StrEnum):
    ADMIN = "admin"
    TEAM_MANAGER = "team_manager"
    MEMBER = "member"
    VIEWER = "viewer"


class Visibility(StrEnum):
    PRIVATE = "private"
    PROJECT = "project"
    TEAM = "team"
    ORGANIZATION = "organization"


class RecordStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class OligoRole(StrEnum):
    FORWARD_PRIMER = "forward_primer"
    REVERSE_PRIMER = "reverse_primer"
    PROBE = "probe"
    INTERNAL_OLIGO = "internal_oligo"
    SEQUENCING_PRIMER = "sequencing_primer"
    ADAPTER = "adapter"
    GUIDE = "guide"
    DONOR = "donor"
    TEMPLATE = "template"
    OTHER = "other"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    SUPERSEDED = "superseded"


class AttachmentScanStatus(StrEnum):
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


class AttachmentPublicationStatus(StrEnum):
    QUARANTINED = "quarantined"
    PUBLISHED = "published"
    REJECTED = "rejected"
    REMOVED = "removed"


class ScientificJobKind(StrEnum):
    OLIGO_PRIMER3_QC = "oligo_primer3_qc"
    ASSAY_PRIMER3_PAIR_COMPATIBILITY = "assay_primer3_pair_compatibility"


class ScientificJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ScientificAttemptStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
