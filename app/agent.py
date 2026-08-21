"""Small, inspectable agentic workflow: planner -> tools -> verifier.

Tools return structured data and never expose hidden model reasoning. This makes
the workflow easy to replace with MCP servers later while remaining local-first.
"""
import re
from app.retrieval import retrieve_chunks, get_local_source
from app.decision_tools import calculate_notice_period, check_missing_information, detect_protected_situation, build_risk


def classify_intent(question: str) -> dict:
    q = question.lower()
    topics = {
        "notice_period": ["notice", "oppsigelsesfrist", "years of service", "ansettelse"],
        "sickness": ["sick", "syk", "sykefravær"],
        "pregnancy_leave": ["pregnant", "pregnancy", "gravid", "parental", "permisjon"],
        "probation": ["probation", "prøvetid"],
        "summary_dismissal": ["immediate", "gross misconduct", "avskjed", "without notice"],
        "justification": ["valid reason", "cause", "saklig", "reason to terminate"],
    }
    matches = [name for name, terms in topics.items() if any(term in q for term in terms)]
    return {"intent": matches[0] if matches else "unknown", "scope": bool(matches)}


def extract_case_signals(situation: str) -> dict:
    q = situation.lower()
    return {
        "protected_situation": any(x in q for x in ("sick", "syk", "pregnant", "gravid", "parental", "permisjon")),
        "immediate_action": any(x in q for x in ("immediate", "without notice", "avskjed", "øyeblikkelig")),
        "has_numeric_facts": bool(re.search(r"\d", situation)),
    }


def extract_case_facts(case) -> dict:
    return {
        "employee_age": case.employee_age,
        "years_employed": case.years_employed,
        "in_probation": case.in_probation,
        "on_sick_leave": case.on_sick_leave,
        "pregnant_or_parental_leave": case.pregnant_or_parental_leave,
        "immediate_dismissal": case.immediate_dismissal,
        "termination_reason_provided": bool(case.termination_reason.strip()),
    }


def run_case_tools(case):
    missing = check_missing_information(case)
    protected = detect_protected_situation(case)
    notice_date = None
    if case.notice_date:
        from datetime import date
        try:
            notice_date = date.fromisoformat(case.notice_date)
        except ValueError:
            missing.append("Varslingsdato må være på formatet YYYY-MM-DD.")
    notice = calculate_notice_period(years_employed=case.years_employed, employee_age=case.employee_age, in_probation=case.in_probation, notice_date=notice_date)
    risk = build_risk(case, missing, protected)
    return {"facts": extract_case_facts(case), "missing": missing, "protected": protected, "notice": notice, "risk": risk}


def run_retrieval_workflow(question: str, top_k: int = 4):
    intent = classify_intent(question)
    chunks = retrieve_chunks(question, top_k=top_k)
    required_provisions = {
        "notice_period": "§ 15-3",
        "probation": "§ 15-6",
        "justification": "§ 15-7",
        "sickness": "§ 15-8",
        "pregnancy_leave": "§ 15-9",
        "summary_dismissal": "§ 15-14",
    }
    provision = required_provisions.get(intent["intent"])
    if provision and not any(provision in chunk["source_name"] for chunk in chunks):
        source = get_local_source(provision)
        if source:
            chunks = [source] + chunks
    return chunks, {"tools": ["classify_termination_intent", "retrieve_legal_sources"], "intent": intent, "retrieved": len(chunks), "source_guarantee": provision or "none"}
