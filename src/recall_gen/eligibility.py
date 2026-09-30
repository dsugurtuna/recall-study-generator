"""Eligibility filtering module.

Applies multi-stage exclusion criteria for recall study participation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .designer import ParticipantRecord


@dataclass
class ExclusionStage:
    """A single exclusion criterion."""

    name: str
    predicate: Callable[[ParticipantRecord], bool]
    description: str = ""


@dataclass
class EligibilityResult:
    """Eligibility filtering outcome."""

    total_input: int = 0
    total_eligible: int = 0
    excluded_per_stage: dict[str, int] = field(default_factory=dict)
    eligible_ids: list[str] = field(default_factory=list)

    @property
    def exclusion_rate(self) -> float:
        if self.total_input == 0:
            return 0.0
        return 1.0 - (self.total_eligible / self.total_input)


class EligibilityFilter:
    """Multi-stage eligibility filter.

    Stages are applied sequentially. A participant excluded by
    an earlier stage is not re-evaluated in later stages.
    """

    def __init__(self) -> None:
        self.stages: list[ExclusionStage] = []

    def add_stage(
        self,
        name: str,
        predicate: Callable[[ParticipantRecord], bool],
        description: str = "",
    ) -> EligibilityFilter:
        """Add an exclusion stage.

        The predicate should return True if the participant is EXCLUDED.
        """
        self.stages.append(ExclusionStage(name=name, predicate=predicate, description=description))
        return self

    def apply(self, participants: list[ParticipantRecord]) -> EligibilityResult:
        """Apply all stages sequentially."""
        result = EligibilityResult(total_input=len(participants))
        remaining = list(participants)

        for stage in self.stages:
            excluded_ids: set[str] = set()
            kept: list[ParticipantRecord] = []
            for p in remaining:
                if stage.predicate(p):
                    excluded_ids.add(p.participant_id)
                else:
                    kept.append(p)
            result.excluded_per_stage[stage.name] = len(excluded_ids)
            remaining = kept

        result.total_eligible = len(remaining)
        result.eligible_ids = [p.participant_id for p in remaining]
        return result
