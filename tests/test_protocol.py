"""Tests for ProtocolGenerator."""

import csv
import json

from recall_gen.designer import StudyDesign
from recall_gen.protocol import ProtocolGenerator


def _make_design():
    return StudyDesign(
        study_name="APOE Recall",
        target_per_group=50,
        groups={"e3/e3": ["P001", "P002"], "e3/e4": ["P003"]},
        total_selected=3,
    )


class TestProtocolGenerator:
    def test_generate(self):
        gen = ProtocolGenerator()
        protocol = gen.generate(_make_design())
        assert protocol.study_name == "APOE Recall"
        assert protocol.total_participants == 3
        assert "objective" in protocol.sections

    def test_export_participant_list(self, tmp_path):
        out = tmp_path / "participants.csv"
        ProtocolGenerator.export_participant_list(_make_design(), out)
        with open(out) as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["genotype_group"] in ("e3/e3", "e3/e4")

    def test_export_protocol_json(self, tmp_path):
        gen = ProtocolGenerator()
        protocol = gen.generate(_make_design())
        out = tmp_path / "protocol.json"
        ProtocolGenerator.export_protocol_json(protocol, out)
        data = json.loads(out.read_text())
        assert data["study_name"] == "APOE Recall"
        assert data["total_participants"] == 3

    def test_custom_sections(self):
        gen = ProtocolGenerator(template_sections={"custom": "Custom section."})
        protocol = gen.generate(_make_design())
        assert "custom" in protocol.sections

    def test_blinded_export_has_no_group(self, tmp_path):
        out = tmp_path / "blinded.csv"
        ProtocolGenerator.export_participant_list(_make_design(), out, blinded=True)
        lines = out.read_text().splitlines()
        assert lines == ["participant_id", "P001", "P002", "P003"]

    def test_default_protocol_does_not_claim_matched_controls(self):
        protocol = ProtocolGenerator().generate(_make_design())
        assert "matched" not in protocol.sections["design"]
