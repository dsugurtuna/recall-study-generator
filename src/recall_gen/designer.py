"""Study design module.

Creates balanced recall study cohorts by genotype group,
applying stratification by age, sex, and ethnicity.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParticipantRecord:
    """Minimal participant record for study design."""

    participant_id: str
    genotype_group: str
    age: int = 0
    sex: str = ""
    ethnicity: str = ""
    consent_status: str = "active"


@dataclass
class StudyDesign:
    """Finalised study design with cohort assignments."""

    study_name: str = ""
    target_per_group: int = 0
    groups: dict[str, list[str]] = field(default_factory=dict)
    total_selected: int = 0
    balance_summary: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def group_sizes(self) -> dict[str, int]:
        return {g: len(ids) for g, ids in self.groups.items()}


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
        Required consent status.
    """

    def __init__(
        self,
        target_per_group: int = 50,
        min_age: int = 18,
        max_age: int = 80,
        required_consent: str = "active",
    ) -> None:
        self.target_per_group = target_per_group
        self.min_age = min_age
        self.max_age = max_age
        self.required_consent = required_consent

    def _is_eligible(self, p: ParticipantRecord) -> bool:
        if p.consent_status != self.required_consent:
            return False
        return not (p.age < self.min_age or p.age > self.max_age)

    def design(
        self,
        participants: list[ParticipantRecord],
        study_name: str = "Recall Study",
    ) -> StudyDesign:
        """Generate a balanced study design.

        Selects up to target_per_group eligible participants per
        genotype group, prioritising age/sex balance.
        """
        eligible: dict[str, list[ParticipantRecord]] = {}
        for p in participants:
            if self._is_eligible(p):
                eligible.setdefault(p.genotype_group, []).append(p)

        design = StudyDesign(
            study_name=study_name,
            target_per_group=self.target_per_group,
        )

        for group, pool in eligible.items():
            pool.sort(key=lambda p: p.age)
            selected = pool[: self.target_per_group]
            design.groups[group] = [p.participant_id for p in selected]

            sex_counts: dict[str, int] = {}
            for p in selected:
                sex_counts[p.sex] = sex_counts.get(p.sex, 0) + 1
            design.balance_summary[group] = sex_counts

        design.total_selected = sum(len(ids) for ids in design.groups.values())
        return design
