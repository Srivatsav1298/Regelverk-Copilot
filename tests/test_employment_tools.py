from app.decision_tools import calculate_employment_rule, check_contract_fields


def test_contract_check_is_completeness_only_and_requires_review():
    result = check_contract_fields({"parties": "A/B", "role": "Developer"})
    assert result["status"] == "incomplete"
    assert "pay" in result["missing_fields"]
    assert result["review_required"] is True


def test_unknown_calculator_rule_is_safe():
    result = calculate_employment_rule("not_a_rule", {})
    assert result["status"] == "unsupported"


def test_working_time_calculator_does_not_guess_without_facts():
    result = calculate_employment_rule("working_time_check", {})
    assert result["status"] == "unknown"
    assert result["missing"]
