"""Agentic legal workflow: intent routing -> retrieval -> domain tools -> verifier.

Tools return structured data and transport-neutral contracts suitable
for direct API invocation and MCP endpoints.
"""

import re
import logging
from typing import Any, Dict, List, Tuple
from app.retrieval import retrieve_chunks, get_local_source
from app.decision_tools import calculate_notice_period, check_missing_information, detect_protected_situation, build_risk
from app.source_manifest import DOMAIN_CATALOG

logger = logging.getLogger("regelverk-copilot.agent")


def classify_intent(question: str, conversation_context: list[dict] | None = None) -> dict:
    conversation_context = conversation_context or []
    prior_user_text = " ".join(turn.get("content", "") for turn in conversation_context if turn.get("role") == "user")
    q = f"{prior_user_text} {question}".lower()

    # Detailed intent mapping covering termination, contracts, working hours, leave, holidays, disputes, workplace rights
    topics = {
        "discussion_meeting": ["drøfting", "drøftingsmøte", "15-1", "discussion meeting", "før oppsigelse"],
        "mass_redundancy": ["masseoppsigelse", "15-2", "collective redundancy", "10 ansatte", "varsel til nav"],
        "notice_period": ["notice", "oppsigelsesfrist", "oppsigelsestid", "15-3", "frister", "hvor lang frist", "ansiennitet"],
        "form_requirements": ["formkrav", "skriftlig oppsigelse", "verbal notice", "15-4", "formfeil", "15-5", "rekommandert", "hva må stå i oppsigelsen", "writing"],
        "probation": ["probation", "prøvetid", "15-6", "oppsigelse i prøvetid", "prøvetidsperiode"],
        "justification": ["saklig", "saklig grunn", "usaklig", "nedbemanning", "downsizing", "15-7", "driftsinnskrenkning", "valid reason", "objective justification", "objectively justified", "cause", "annet passende arbeid"],
        "sickness": ["sick", "syk", "sykefravær", "sykemeldt", "15-8", "oppsigelsesvern ved sykdom", "12 måneder"],
        "pregnancy_leave": ["pregnant", "pregnancy", "gravid", "graviditet", "parental", "foreldrepermisjon", "permisjon", "15-9", "fødsel", "adopsjon"],
        "suspension": ["suspensjon", "suspendere", "suspend", "investigating misconduct", "15-13", "fratre under undersøkelse"],
        "summary_dismissal": ["avskjed", "avskjedige", "immediate", "gross misconduct", "without notice", "15-14", "grovt pliktbrudd"],
        "work_certificate": ["arbeidsattest", "attest", "15-15"],
        "dispute_deadlines": ["forhandling", "forhandlingsmøte", "søksmål", "søksmålsfrist", "17-3", "17-4", "stå i stilling", "tvist"],
        "contract_requirements": ["arbeidsavtale", "kontrakt", "ansettelseskontrakt", "14-5", "14-6", "hva må en kontrakt inneholde"],
        "employee_status": ["oppdragstaker", "arbeidstaker", "konsulent eller ansatt", "1-8", "selvstendig næringsdrivende"],
        "temporary_work": ["midlertidig", "temporary employment", "fixed-term", "vikar", "vikariat", "14-9", "fast ansettelse", "3-årsregel", "4-årsregel"],
        "working_hours": ["arbeidstid", "working-time", "alminnelig arbeidstid", "10-4", "10-8", "hvor mange timer", "rest period", "rest periods", "daily and weekly rest", "skift", "turnus", "pause", "10-9"],
        "overtime": ["overtid", "overtidsarbeid", "10-6", "overtidstillegg", "40 prosent", "pålagt overtid"],
        "holidays": ["ferie", "feriefritid", "ferieloven", "hovedferie", "3 uker", "feriedager", "25 virkedager"],
        "holiday_pay": ["feriepenger", "feriepengeberegning", "10,2 prosent", "10.2%", "10.2 percent", "12,5 prosent", "12.5%", "holiday pay", "holiday-pay", "vacation pay", "sluttoppgjør feriepenger"],
        "whistleblowing": ["varsle", "varsling", "kritikkverdige", "2a-1", "2a-2", "whistleblow"],
        "retaliation": ["gjengjeldelse", "2a-4", "reaksjon på varsling", "straff for å varsle"],
        "harassment": ["trakassering", "psykososialt", "arbeidsmiljø", "4-3", "mobbing", "utilbørlig"],
    }

    matched_intent = next((name for name, terms in topics.items() if any(term in q for term in terms)), None)

    # Historical wording is outside the current corpus unless an as-of version is supplied.
    if any(term in q for term in ("historical", "in 2015", "in 2016", "as it was", "exact wording")):
        matched_intent = None

    # General domain keywords
    domain_terms = {
        "termination": ("oppsigelse", "si opp", "sagt opp", "fratredelse", "avskjed", "nedbemanning", "slutte"),
        "contracts": ("kontrakt", "arbeidsavtale", "ansettelse", "hiring", "onboarding"),
        "working_time": ("arbeidstid", "overtid", "turnus", "vakt", "pause", "hvile"),
        "holidays": ("ferie", "feriepenger", "ferieår"),
        "leave": ("permisjon", "foreldrepermisjon", "gravid"),
        "sickness": ("syk", "sykefravær", "egenmelding", "sykemelding"),
        "workplace_rights": ("varsling", "trakassering", "arbeidsmiljø", "hms", "mobbing"),
        "disputes": ("tvist", "konflikt", "forhandling", "søksmål", "advokat", "retten"),
        "temporary_work": ("midlertidig", "temporary employment", "fixed-term", "temporary", "innleie", "vikar", "bemanningsbyrå"),
    }

    if matched_intent == "employee_status" and any(term in q for term in ("ferie", "feriedag", "ferieloven")):
        matched_intent = "holidays"
    if "verbal notice" in q:
        matched_intent = "form_requirements"

    if matched_intent:
        if matched_intent in ("discussion_meeting", "mass_redundancy", "notice_period", "form_requirements", "probation", "justification", "suspension", "summary_dismissal", "work_certificate"):
            domain = "termination"
        elif matched_intent in ("sickness",):
            domain = "sickness"
        elif matched_intent in ("pregnancy_leave",):
            domain = "leave"
        elif matched_intent in ("dispute_deadlines",):
            domain = "disputes"
        elif matched_intent in ("contract_requirements", "employee_status"):
            domain = "contracts"
        elif matched_intent in ("temporary_work",):
            domain = "temporary_work"
        elif matched_intent in ("working_hours", "overtime"):
            domain = "working_time"
        elif matched_intent in ("holidays", "holiday_pay"):
            domain = "holidays"
        elif matched_intent in ("whistleblowing", "retaliation", "harassment"):
            domain = "workplace_rights"
        else:
            domain = "termination"
    else:
        domain = next((d for d, terms in domain_terms.items() if any(t in q for t in terms)), "unknown")

    catalog = next((item for item in DOMAIN_CATALOG if item["domain"] == domain), None)

    return {
        "intent": matched_intent or ("general_" + domain if domain != "unknown" else "unknown"),
        "domain": domain,
        "scope": domain != "unknown",
        "coverage": catalog or {"status": "unsupported"},
    }


def build_response_plan(question: str, conversation_context: list[dict] | None = None) -> dict:
    """Identify explicit requirements before retrieval and answer generation."""
    conversation_context = conversation_context or []
    prior_user_text = " ".join(turn.get("content", "") for turn in conversation_context if turn.get("role") == "user")
    q = f"{prior_user_text} {question}".lower()
    holiday_pay = any(term in q for term in ("feriepenger", "feriepenge", "holiday pay", "holiday-pay", "vacation pay"))
    asks_calculation = any(term in q for term in ("calculate", "beregn", "beregne", "how much", "hvor mye", "amount", "beløp")) or bool(re.search(r"\d[\d .]*\s*(nok|kr|kroner)|\d[\d,.]*\s*%", q))
    asks_timing = any(term in q for term in ("when", "must it be paid", "payment", "paid", "utbetales", "utbetaling", "når", "frist"))
    amount_matches = re.findall(r"(?:nok|kr|kroner)\s*([0-9]{1,3}(?:[,.][0-9]{3})+|[0-9][0-9 .]*(?:[,.][0-9]{1,2})?)|([0-9]{1,3}(?:[ .][0-9]{3})+(?:[,.][0-9]{1,2})?)\s*(?:nok|kr|kroner)", q)
    amounts = [left or right for left, right in amount_matches]
    if not amounts:
        amounts = re.findall(r"([0-9]{1,3}(?:[,.][0-9]{3})+)\s*(?:nok|kr|kroner)", q)
    rates = re.findall(r"([0-9]+(?:[,.][0-9]+)?)\s*(?:%|prosent|percent)", q)
    age_match = re.search(r"(?:age|alder|år|years old)\s*(?:is|er)?\s*(\d{2})", q)
    employee_age = int(age_match.group(1)) if age_match else None
    plan = {"requested_outcome": question.strip(), "requirements": [], "facts": {}, "legal_issues": [], "required_sources": [], "calculation": None, "context_used": bool(prior_user_text), "conversation_context": conversation_context[-8:], "historical_request": any(term in q for term in ("historical", "in 2015", "in 2016", "as it was", "exact wording"))}
    if holiday_pay:
        plan["required_sources"] = ["Ferieloven § 10", "Ferieloven § 11"]
        plan["legal_issues"] = ["calculation basis and statutory percentage", "normal payment timing"]
        plan["false_premise"] = bool("all" in q and ("12%" in q or "12 %" in q or "12 prosent" in q))
        plan["requirements"].append("explain holiday-pay basis and applicable statutory minimum rate")
        if asks_timing:
            plan["requirements"].append("explain when holiday pay is normally paid")
        if asks_calculation and amounts and rates:
            plan["requirements"].append("show the calculation and result")
        elif asks_calculation and (("how much" in q and ("receive" in q or "will" in q or "får" in q)) or "what amount" in q or re.search(r"\bcalculate\b|\bberegn\b", q)):
            plan["requirements"].append("request missing calculation inputs")
        if amounts:
            raw = amounts[0]
            plan["facts"]["remuneration_nok"] = raw.replace(" ", "").replace(".", "") if " " in raw or (raw.count(".") == 1 and len(raw.split(".")[-1]) == 3) else raw
        if rates:
            plan["facts"]["rate_pct"] = rates[0]
        elif amounts and any(term in q for term in ("statutory", "legal minimum", "lovbestemt", "minimumssats", "minimum rate")):
            plan["facts"]["rate_pct"] = "12.5" if employee_age is not None and employee_age >= 60 else "10.2"
            plan["facts"]["rate_source"] = "Ferieloven § 10"
        if plan["facts"].get("remuneration_nok") and plan["facts"].get("rate_pct"):
            plan["calculation"] = {"operation": "holiday_pay", "remuneration": plan["facts"]["remuneration_nok"], "rate_pct": plan["facts"]["rate_pct"]}
    elif asks_calculation:
        generic_amounts = re.findall(r"(?:nok|kr|kroner)\s*([0-9]{1,3}(?:[,.][0-9]{3})+|[0-9][0-9 .]*(?:[,.][0-9]{1,2})?)|([0-9]{1,3}(?:[,.][0-9]{3})+)\s*(?:nok|kr|kroner)", q)
        generic_rates = rates
        if generic_amounts and generic_rates:
            raw_amount = next(left or right for left, right in generic_amounts)
            plan["calculation"] = {"operation": "percentage", "remuneration": raw_amount, "rate_pct": generic_rates[0]}
            plan["requirements"].append("show the calculation and result")
    return plan


def extract_case_signals(situation: str) -> dict:
    q = situation.lower()
    return {
        "protected_situation": any(x in q for x in ("sick", "syk", "sykmeldt", "pregnant", "gravid", "parental", "permisjon")),
        "immediate_action": any(x in q for x in ("immediate", "without notice", "avskjed", "øyeblikkelig", "grovt pliktbrudd")),
        "discussion_held": any(x in q for x in ("drøftingsmøte", "drøftet", "møte med tillitsvalgt")),
        "downsizing": any(x in q for x in ("nedbemanning", "driftsinnskrenkning", "overtallig")),
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


def run_retrieval_workflow(question: str, top_k: int = 4, conversation_context: list[dict] | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    conversation_context = conversation_context or []
    prior_user_text = " ".join(turn.get("content", "") for turn in conversation_context if turn.get("role") == "user")
    retrieval_question = f"{question} {prior_user_text}".strip()
    intent = classify_intent(question, conversation_context)
    plan = build_response_plan(question, conversation_context)
    domain = intent.get("domain") if intent.get("domain") != "unknown" else None
    retrieval_status = "retrieved"
    try:
        chunks = retrieve_chunks(retrieval_question, top_k=top_k, domain=domain)
    except Exception as exc:
        logger.warning("Legal source retrieval failed (%s: %s)", type(exc).__name__, exc)
        chunks = []
        retrieval_status = "unavailable"
    if not chunks and retrieval_status != "unavailable":
        retrieval_status = "no_match"

    # Provision guarantees for known intents
    provision_map = {
        "discussion_meeting": "§ 15-1",
        "mass_redundancy": "§ 15-2",
        "notice_period": "§ 15-3",
        "form_requirements": "§ 15-4",
        "probation": "§ 15-6",
        "justification": "§ 15-7",
        "sickness": "§ 15-8",
        "pregnancy_leave": "§ 15-9",
        "suspension": "§ 15-13",
        "summary_dismissal": "§ 15-14",
        "work_certificate": "§ 15-15",
        "dispute_deadlines": "§ 17-3",
        "contract_requirements": "§ 14-6",
        "employee_status": "§ 1-8",
        "temporary_work": "§ 14-9",
        "working_hours": "§ 10-4",
        "overtime": "§ 10-6",
        "holidays": "Ferieloven § 5",
        "holiday_pay": "Ferieloven § 10",
        "whistleblowing": "§ 2A-1",
        "retaliation": "§ 2A-4",
        "harassment": "§ 4-3",
    }

    required_provisions = list(plan.get("required_sources", []))
    target_prov = provision_map.get(intent.get("intent"))
    if target_prov and target_prov not in required_provisions:
        required_provisions.insert(0, target_prov)
    for provision in required_provisions:
        if not any(provision in c["source_name"] for c in chunks):
            exact_chunk = get_local_source(provision)
            if exact_chunk:
                chunks = [exact_chunk] + chunks[:max(top_k - 1, 0)]

    return chunks, {
        "tools": ["classify_employment_question", "retrieve_legal_sources"],
        "intent": intent,
        "retrieved": len(chunks),
        "source_guarantee": required_provisions or (target_prov or "none"),
        "response_plan": plan,
        "retrieval_query": retrieval_question,
        "retrieval_status": retrieval_status,
    }
