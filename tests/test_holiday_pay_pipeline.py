from app.agent import build_response_plan, run_retrieval_workflow
from app.cache import _make_key
from app.decision_tools import calculate_holiday_pay_amount
from app.llm import generate_answer


def answer_for(question: str, language: str = "en"):
    chunks, workflow = run_retrieval_workflow(question)
    return generate_answer(question, chunks, language, plan=workflow["response_plan"]), workflow


def test_holiday_pay_example_calculates_and_explains_payment_timing():
    result, workflow = answer_for(
        "An employee earned NOK 600,000 in qualifying remuneration last year. "
        "Calculate their statutory holiday pay at 10.2% and explain when it must be paid."
    )
    assert "NOK 600,000 × 10.2% = NOK 61,200" in result.answer
    assert "last ordinary payday before the holiday" in result.answer
    assert "Ferieloven § 10" in result.answer
    assert "Ferieloven § 11" in result.answer
    assert workflow["response_plan"]["calculation"]["remuneration"] == "600,000"


def test_holiday_pay_general_question_covers_rate_and_deadline():
    result, _ = answer_for("How is holiday pay calculated in Norway, what is the minimum statutory rate, and when must it normally be paid?")
    assert "10.2%" in result.answer
    assert "last ordinary payday before the holiday" in result.answer
    assert result.calculation_results == {}


def test_arithmetic_only_question_does_not_require_legal_retrieval():
    result, _ = answer_for("Calculate 12% of NOK 600,000. Give only the calculation and result.")
    assert result.answer == "NOK 600,000 × 12% = NOK 72,000"
    assert result.citations == []


def test_missing_holiday_pay_inputs_are_requested_not_invented():
    result, _ = answer_for("How much holiday pay will this employee receive?")
    assert "need" in result.answer.lower()
    assert "remuneration" in result.answer.lower()
    assert result.calculation_results == {}


def test_user_supplied_rate_is_calculated_but_not_treated_as_universal_law():
    result, _ = answer_for("Since all Norwegian employees receive exactly 12% holiday pay by law, calculate the amount on NOK 600,000.")
    assert "NOK 600,000 × 12% = NOK 72,000" in result.answer
    assert "not universally required by statute" in result.answer


def test_decimal_money_calculation_is_exact():
    result = calculate_holiday_pay_amount(remuneration="600000", rate_pct="10.2")
    assert result["amount_nok"] == 61200.0
    assert result["formula"] == "NOK 600,000 × 10.2% = NOK 61,200"


def test_cache_context_changes_key():
    assert _make_key("same question", "employee") != _make_key("same question", "employer")


def test_api_returns_calculation_and_official_source_urls(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main

    monkeypatch.setattr(main, "source_freshness", lambda: {"status": "current", "verified_corpus_allowed": True})
    response = TestClient(main.app).post("/api/v1/ask", json={
        "question": "An employee earned NOK 600,000 in qualifying remuneration last year. Calculate their statutory holiday pay at 10.2% and explain when it must be paid.",
        "language": "en",
        "include_trace": True,
    })
    assert response.status_code == 200
    payload = response.json()
    assert "NOK 600,000 × 10.2% = NOK 61,200" in payload["answer"]
    assert all(item["url"] == "https://lovdata.no/lov/1988-04-29-21" for item in payload["citations"])
