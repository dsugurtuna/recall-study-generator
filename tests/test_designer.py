"""Tests for StudyDesigner and EligibilityFilter."""

from recall_gen.designer import ParticipantRecord, StudyDesigner
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
        for _group, ids in design.groups.items():
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


def _pool(group: str, specs: list[tuple[str, int, str]]) -> list[ParticipantRecord]:
    return [ParticipantRecord(pid, group, age=age, sex=sex) for pid, age, sex in specs]


class TestBalancing:
    def test_selection_spans_age_range_not_youngest(self):
        # Ten eligible participants aged 20..65; pick 3.
        people = _pool("A", [(f"P{i:02d}", 20 + 5 * i, "F") for i in range(10)])
        design = StudyDesigner(target_per_group=3).design(people)
        assert design.age_range["A"] == (20, 65)
        assert design.groups["A"] == ["P00", "P05", "P09"]

    def test_sexes_balanced_when_pool_allows(self):
        people = _pool(
            "A",
            [(f"M{i}", 30 + i, "M") for i in range(8)] + [(f"F{i}", 30 + i, "F") for i in range(3)],
        )
        design = StudyDesigner(target_per_group=4).design(people)
        assert design.balance_summary["A"] == {"F": 2, "M": 2}

    def test_short_stratum_gives_slots_to_other(self):
        people = _pool("A", [(f"M{i}", 30 + i, "M") for i in range(8)] + [("F0", 40, "F")])
        design = StudyDesigner(target_per_group=5).design(people)
        assert design.balance_summary["A"] == {"F": 1, "M": 4}

    def test_shortfall_recorded(self):
        people = _pool("A", [("P1", 40, "F"), ("P2", 50, "M")])
        design = StudyDesigner(target_per_group=5).design(people)
        assert design.shortfall == {"A": 3}

    def test_deterministic(self):
        people = _make_participants()
        d1 = StudyDesigner(target_per_group=1).design(people)
        d2 = StudyDesigner(target_per_group=1).design(list(reversed(people)))
        assert d1.groups == d2.groups

    def test_invalid_age_bounds(self):
        import pytest

        with pytest.raises(ValueError):
            StudyDesigner(min_age=60, max_age=40)


def test_eligibility_result_feeds_designer():
    ef = EligibilityFilter().add_stage("withdrawn", lambda p: p.consent_status == "withdrawn")
    result = ef.apply(_make_participants())
    assert [p.participant_id for p in result.eligible] == result.eligible_ids
    design = StudyDesigner(target_per_group=10).design(result.eligible)
    assert "P009" not in [pid for ids in design.groups.values() for pid in ids]
