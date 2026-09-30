"""Protocol generation module.

Produces structured recall study protocol documents from study designs.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from .designer import StudyDesign


@dataclass
class StudyProtocol:
    """Generated study protocol."""

    study_name: str = ""
    version: str = "1.0"
    groups: dict[str, list[str]] = field(default_factory=dict)
    total_participants: int = 0
    sections: dict[str, str] = field(default_factory=dict)


class ProtocolGenerator:
    """Generate structured recall study protocols.

    Parameters
    ----------
    template_sections : dict, optional
        Section templates for the protocol document.
    """

    DEFAULT_SECTIONS: ClassVar[dict[str, str]] = {
        "objective": "Investigate genotype-phenotype associations through targeted recall.",
        "design": "Genotype groups, each balanced on sex and spread across the age range.",
        "eligibility": "Consented biobank participants within specified age range.",
        "procedures": "Participant invitation, consent verification, phenotyping visit.",
        "data_handling": "All data handled in accordance with institutional governance.",
    }

    def __init__(
        self,
        template_sections: dict[str, str] | None = None,
    ) -> None:
        self.sections = template_sections or dict(self.DEFAULT_SECTIONS)

    def generate(self, design: StudyDesign) -> StudyProtocol:
        """Generate protocol from a study design."""
        protocol = StudyProtocol(
            study_name=design.study_name,
            groups=design.groups,
            total_participants=design.total_selected,
            sections=dict(self.sections),
        )
        return protocol

    @staticmethod
    def export_participant_list(
        design: StudyDesign,
        output_path: str | Path,
        blinded: bool = False,
    ) -> None:
        """Export participant assignments to CSV.

        With ``blinded=True`` the file has participant IDs only, sorted by
        ID, so staff who invite participants cannot infer genotype group
        from either a column or the row order.
        """
        with open(output_path, "w", newline="") as fh:
            writer = csv.writer(fh)
            if blinded:
                writer.writerow(["participant_id"])
                all_ids = sorted(pid for ids in design.groups.values() for pid in ids)
                for pid in all_ids:
                    writer.writerow([pid])
                return
            writer.writerow(["participant_id", "genotype_group"])
            for group, ids in sorted(design.groups.items()):
                for pid in sorted(ids):
                    writer.writerow([pid, group])

    @staticmethod
    def export_protocol_json(
        protocol: StudyProtocol,
        output_path: str | Path,
    ) -> None:
        """Export protocol to JSON."""
        data = {
            "study_name": protocol.study_name,
            "version": protocol.version,
            "total_participants": protocol.total_participants,
            "groups": {g: len(ids) for g, ids in protocol.groups.items()},
            "sections": protocol.sections,
        }
        with open(output_path, "w") as fh:
            json.dump(data, fh, indent=2)
