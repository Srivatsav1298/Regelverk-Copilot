"""Tests for deterministic legal decision tools across multiple employment law categories."""

from datetime import date
from app.decision_tools import (
    calculate_notice_period,
    check_contract_fields,
    check_working_time,
    calculate_holiday_details,
    check_termination_notice_form,
    calculate_employment_rule,
)


def test_notice_period_calculation_bounds():
    # 5 years -> 2 months
    res5 = calculate_notice_period(years_employed=6)
    assert res5["months_or_days"] == 2
    assert "to måneder" in res5["label"]

    # 10 years, age 56 -> 5 months
    res56 = calculate_notice_period(years_employed=11, employee_age=56)
    assert res56["months_or_days"] == 5
    assert "fem måneder" in res56["label"]

    # Start date calculation
    dated = calculate_notice_period(years_employed=2, notice_date=date(2026, 3, 15))
    assert dated["notice_start"] == "2026-04-01"
    assert dated["period_end"] == "2026-04-30"


def test_contract_audit_flags_missing_statutory_clauses():
    # Incomplete contract
    incomplete = check_contract_fields({"parties": "Bedrift AS og Ola", "role": "Utvikler"})
    assert incomplete["status"] == "incomplete"
    assert "pay" in incomplete["missing_fields"]
    assert "notice" in incomplete["missing_fields"]

    # Complete contract
    complete = check_contract_fields({
        "parties": "Bedrift AS og Ola",
        "workplace": "Oslo",
        "role": "Utvikler",
        "start_date": "2026-01-01",
        "pay": "600 000 NOK",
        "working_time": "37.5 timer/uke",
        "holiday": "25 dager",
        "notice": "1 måned",
    })
    assert complete["status"] == "ready_for_review"
    assert len(complete["missing_fields"]) == 0


def test_working_time_and_overtime_checker():
    # Over 40 hours -> violation
    res = check_working_time(hours_per_week=48, consecutive_days=5)
    assert res["status"] == "violation"
    assert any("40 timer" in v for v in res["violations"])

    # 7 consecutive days without rest -> violation
    res_days = check_working_time(hours_per_week=37.5, consecutive_days=7)
    assert res_days["status"] == "violation"
    assert any("35 timer" in v for v in res_days["violations"])


def test_holiday_entitlement_and_pay_calculation():
    # Standard employee under 60
    young = calculate_holiday_details(salary_basis=500000, employee_age=35)
    assert young["vacation_days_statutory"] == 25
    assert young["holiday_pay_rate_pct"] == 10.2
    assert young["estimated_holiday_pay_nok"] == 51000.0

    # Senior employee (60+)
    senior = calculate_holiday_details(salary_basis=500000, employee_age=62)
    assert senior["vacation_days_statutory"] == 31
    assert senior["holiday_pay_rate_pct"] == 12.5
    assert senior["estimated_holiday_pay_nok"] == 62500.0


def test_termination_notice_form_audit():
    # Defective notice (e.g. oral or missing statutory negotiation/lawsuit info)
    defective = check_termination_notice_form({
        "written": True,
        "personal_or_registered": True,
        "negotiation_rights": False,  # Missing!
        "lawsuit_rights": False,      # Missing!
    })
    assert defective["status"] == "defective"
    assert defective["is_formally_valid"] is False
    assert len(defective["missing_mandatory_elements"]) >= 2
    assert "§ 15-5" in defective["consequence_of_defect"]

    # Valid notice
    valid = check_termination_notice_form({
        "written": True,
        "personal_or_registered": True,
        "negotiation_rights": True,
        "lawsuit_rights": True,
        "stay_in_post_rights": True,
        "correct_defendant": True,
    })
    assert valid["status"] == "valid"
    assert valid["is_formally_valid"] is True
