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
