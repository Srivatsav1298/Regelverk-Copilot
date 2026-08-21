from datetime import date

from app.decision_tools import calculate_notice_period, check_missing_information, detect_protected_situation
from app.schemas import CaseAssessmentRequest


def test_notice_period_tenure_and_age_bands():
    assert calculate_notice_period(years_employed=4, employee_age=40)["label"] == "én måned"
    assert calculate_notice_period(years_employed=5, employee_age=40)["label"] == "to måneder"
    assert calculate_notice_period(years_employed=10, employee_age=56)["label"] == "fem måneder"
    assert calculate_notice_period(years_employed=10, employee_age=61)["label"] == "seks måneder"


def test_probation_is_fourteen_days():
    result = calculate_notice_period(years_employed=1, employee_age=30, in_probation=True)
    assert result["label"] == "14 dager"
    assert result["provision"].endswith("(7)")


def test_notice_period_starts_next_month_and_ends_at_month_end():
    result = calculate_notice_period(years_employed=2, employee_age=30, notice_date=date(2026, 8, 20))
    assert result["notice_start"] == "2026-09-01"
    assert result["period_end"] == "2026-09-30"


def test_protected_situation_and_missing_facts():
    case = CaseAssessmentRequest(situation="Employee is sick", on_sick_leave=True)
    assert detect_protected_situation(case)["protected"] is True
    missing = check_missing_information(case)
    assert any("Ansettelsestid" in item for item in missing)
    assert any("grunnlag" in item.lower() for item in missing)


def test_contradictory_protection_flags_are_called_out():
    case = CaseAssessmentRequest(situation="Leave case", on_sick_leave=True, pregnant_or_parental_leave=True)
    assert any("bland" in item for item in check_missing_information(case))
