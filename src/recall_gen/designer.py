"""Study design module.

Selects participants into genotype groups for a recall-by-genotype study.
Within each group, selection is balanced on sex and spread across the age
range, so that groups are comparable and not skewed towards one end.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class ParticipantRecord:
    """Minimal participant record for study design."""

    participant_id: str
    genotype_group: str
    age: int = 0
    sex: str = ""
    ethnicity: str = ""  # carried through; not used for selection
    consent_status: str = "active"


@dataclass
class StudyDesign:
    """Finalised study design with cohort assignments."""

    study_name: str = ""
    target_per_group: int = 0
    groups: dict[str, list[str]] = field(default_factory=dict)
    total_selected: int = 0
    balance_summary: dict[str, dict[str, int]] = field(default_factory=dict)  # sex counts
    age_range: dict[str, tuple[int, int]] = field(default_factory=dict)  # (min, max)
    shortfall: dict[str, int] = field(default_factory=dict)  # target minus selected

    @property
    def group_sizes(self) -> dict[str, int]:
        return {g: len(ids) for g, ids in self.groups.items()}


def _spread_by_age(pool: list[ParticipantRecord], k: int) -> list[ParticipantRecord]:
    """Pick k participants evenly spaced across the age-sorted pool.

    Deterministic: ties on age are broken by participant ID. Uses
    floor(x + 0.5) so that indices are strictly increasing and distinct.
    """
    ordered = sorted(pool, key=lambda p: (p.age, p.participant_id))
    n = len(ordered)
    if k >= n:
        return ordered
    if k <= 0:
        return []
    if k == 1:
        return [ordered[(n - 1) // 2]]
    step = (n - 1) / (k - 1)
    return [ordered[math.floor(i * step + 0.5)] for i in range(k)]


def _allocate(capacity: dict[str, int], total: int) -> dict[str, int]:
    """Share ``total`` slots across strata as evenly as capacity allows.

    Slots are handed out one at a time, round-robin in sorted stratum
    order, skipping strata that are full. The result is the most even split
    possible given how many eligible people each stratum has.
    """
    alloc = dict.fromkeys(capacity, 0)
    remaining = min(total, sum(capacity.values()))
    strata = sorted(capacity)
    while remaining > 0:
        for s in strata:
            if remaining == 0:
                break
            if alloc[s] < capacity[s]:
                alloc[s] += 1
                remaining -= 1
    return alloc


class StudyDesigner:
    """Design genotype-stratified recall studies.

    Parameters
    ----------
    target_per_group : int
        Target participants per genotype group.
    min_age : int
        Minimum participant age (inclusive).
    max_age : int
        Maximum participant age (inclusive).
    required_consent : str
        Consent status a participant must have to be selected.
    """

    def __init__(
        self,
        target_per_group: int = 50,
        min_age: int = 18,
        max_age: int = 80,
        required_consent: str = "active",
    ) -> None:
        if target_per_group < 0:
            raise ValueError("target_per_group must be non-negative")
        if min_age > max_age:
            raise ValueError("min_age must not exceed max_age")
        self.target_per_group = target_per_group
        self.min_age = min_age
        self.max_age = max_age
        self.required_consent = required_consent

    def _is_eligible(self, p: ParticipantRecord) -> bool:
        if p.consent_status != self.required_consent:
            return False
        return self.min_age <= p.age <= self.max_age

    def design(
        self,
        participants: list[ParticipantRecord],
        study_name: str = "Recall Study",
    ) -> StudyDesign:
        """Generate a design with up to ``target_per_group`` per genotype group.

        Within each group: slots are split across sexes as evenly as the
        eligible pool allows, then each sex stratum is sampled evenly across
        its age range. Groups with too few eligible participants are
        recorded in ``shortfall`` rather than padded.
        """
        eligible: dict[str, list[ParticipantRecord]] = {}
        for p in participants:
            if self._is_eligible(p):
                eligible.setdefault(p.genotype_group, []).append(p)

        design = StudyDesign(study_name=study_name, target_per_group=self.target_per_group)

        for group in sorted(eligible):
            pool = eligible[group]
            by_sex: dict[str, list[ParticipantRecord]] = {}
            for p in pool:
                by_sex.setdefault(p.sex, []).append(p)

            alloc = _allocate({s: len(v) for s, v in by_sex.items()}, self.target_per_group)
            selected: list[ParticipantRecord] = []
            for sex in sorted(by_sex):
                selected.extend(_spread_by_age(by_sex[sex], alloc[sex]))

            design.groups[group] = sorted(p.participant_id for p in selected)
            sex_counts: dict[str, int] = {}
            for p in selected:
                sex_counts[p.sex] = sex_counts.get(p.sex, 0) + 1
            design.balance_summary[group] = sex_counts
            if selected:
                ages = [p.age for p in selected]
                design.age_range[group] = (min(ages), max(ages))
            short = self.target_per_group - len(selected)
            if short > 0:
                design.shortfall[group] = short

        design.total_selected = sum(len(ids) for ids in design.groups.values())
        return design
