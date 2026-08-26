from __future__ import annotations

from dataclasses import dataclass

from oligospace_api.services.sequence_analysis import normalize_sequence, reverse_complement


@dataclass(frozen=True, order=True)
class SequenceMatch:
    start: int
    end: int
    strand: str


@dataclass(frozen=True)
class MappingResult:
    matches: tuple[SequenceMatch, ...]
    match_count: int
    ambiguous: bool
    warning: str | None
    algorithm: str = "exact-substring-both-strands/v1"


def _find_all(haystack: str, needle: str) -> list[int]:
    starts: list[int] = []
    offset = 0
    while True:
        index = haystack.find(needle, offset)
        if index < 0:
            return starts
        starts.append(index)
        offset = index + 1


def map_exact(oligo_sequence: str, target_sequence: str) -> MappingResult:
    oligo = normalize_sequence(oligo_sequence)
    target = normalize_sequence(target_sequence)
    reverse = reverse_complement(oligo)
    matches = [SequenceMatch(start, start + len(oligo), "+") for start in _find_all(target, oligo)]
    if reverse != oligo:
        matches.extend(
            SequenceMatch(start, start + len(oligo), "-") for start in _find_all(target, reverse)
        )
    matches.sort()
    count = len(matches)
    if count == 0:
        warning = "No exact match in the supplied target sequence."
    elif count > 1:
        warning = f"Ambiguous mapping: {count} exact matches in the supplied target sequence."
    else:
        warning = None
    return MappingResult(tuple(matches), count, count > 1, warning)
