"""Tests for StudyDesigner and EligibilityFilter."""

from recall_gen.designer import StudyDesigner, ParticipantRecord
from recall_gen.eligibility import EligibilityFilter


def _make_participants():
    return [
        ParticipantRecord("P001", "e3/e3", age=45, sex="M"),
        ParticipantRecord("P002", "e3/e3", age=55, sex="F"),
        ParticipantRecord("P003", "e3/e4", age=30, sex="M"),
        ParticipantRecord("P004", "e3/e4", age=65, sex="F"),
        ParticipantRecord("P005", "e4/e4", age=50, sex="M"),
        ParticipantRecord("P006", "e4/e4", age=70, sex="F"),
        ParticipantRecord("P007", "e3/e3", age=15, sex="M"),  # under-age
        ParticipantRecord("P008", "e3/e3", age=85, sex="F"),  # over-age
        ParticipantRecord("P009", "e3/e4", age=40, sex="M", consent_status="withdrawn"),
    ]


class TestStudyDesigner:
    def test_basic_design(self):
        designer = StudyDesigner(target_per_group=2, min_age=18, max_age=80)
        design = designer.design(_make_participants(), "Test Study")
        assert design.study_name == "Test Study"
        assert design.total_selected > 0

    def test_age_filtering(self):
        designer = StudyDesigner(target_per_group=10, min_age=18, max_age=80)
        design = designer.design(_make_participants())
        all_ids = []
        for ids in design.groups.values():
            all_ids.extend(ids)
        assert "P007" not in all_ids
        assert "P008" not in all_ids

    def test_consent_filtering(self):
        designer = StudyDesigner(target_per_group=10)
        design = designer.design(_make_participants())
        all_ids = []
        for ids in design.groups.values():
            all_ids.extend(ids)
        assert "P009" not in all_ids

    def test_target_per_group(self):
        designer = StudyDesigner(target_per_group=1)
        design = designer.design(_make_participants())
        for group, ids in design.groups.items():
            assert len(ids) <= 1

    def test_group_sizes(self):
        designer = StudyDesigner(target_per_group=5)
        design = designer.design(_make_participants())
        sizes = design.group_sizes
        assert isinstance(sizes, dict)
        assert all(isinstance(v, int) for v in sizes.values())


class TestEligibilityFilter:
    def test_single_stage(self):
        ef = EligibilityFilter()
        ef.add_stage("under_18", lambda p: p.age < 18)
        result = ef.apply(_make_participants())
        assert "P007" not in result.eligible_ids
        assert result.excluded_per_stage["under_18"] == 1

    def test_multiple_stages(self):
        ef = EligibilityFilter()
        ef.add_stage("under_18", lambda p: p.age < 18)
        ef.add_stage("over_80", lambda p: p.age > 80)
        ef.add_stage("withdrawn", lambda p: p.consent_status == "withdrawn")
        result = ef.apply(_make_participants())
        assert result.total_eligible == 6
        assert result.exclusion_rate > 0

    def test_zero_input(self):
        ef = EligibilityFilter()
        result = ef.apply([])
        assert result.exclusion_rate == 0.0
        assert result.total_eligible == 0
