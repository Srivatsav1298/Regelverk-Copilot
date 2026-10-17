"""Agentic legal workflow: intent routing -> retrieval -> domain tools -> verifier.

Tools return structured data and transport-neutral contracts suitable
for direct API invocation and MCP endpoints.
"""

import re
from typing import Any, Dict, List, Tuple
from app.retrieval import retrieve_chunks, get_local_source
from app.decision_tools import calculate_notice_period, check_missing_information, detect_protected_situation, build_risk
from app.source_manifest import DOMAIN_CATALOG


def classify_intent(question: str) -> dict:
    q = question.lower()

    # Detailed intent mapping covering termination, contracts, working hours, leave, holidays, disputes, workplace rights
    topics = {
        "discussion_meeting": ["drøfting", "drøftingsmøte", "15-1", "discussion meeting", "før oppsigelse"],
        "mass_redundancy": ["masseoppsigelse", "15-2", "collective redundancy", "10 ansatte", "varsel til nav"],
        "notice_period": ["notice", "oppsigelsesfrist", "oppsigelsestid", "15-3", "frister", "hvor lang frist", "ansiennitet"],
        "form_requirements": ["formkrav", "skriftlig oppsigelse", "15-4", "formfeil", "15-5", "rekommandert", "hva må stå i oppsigelsen"],
        "probation": ["probation", "prøvetid", "15-6", "oppsigelse i prøvetid", "prøvetidsperiode"],
        "justification": ["saklig", "saklig grunn", "usaklig", "nedbemanning", "15-7", "driftsinnskrenkning", "valid reason", "cause", "annet passende arbeid"],
        "sickness": ["sick", "syk", "sykefravær", "sykemeldt", "15-8", "oppsigelsesvern ved sykdom", "12 måneder"],
        "pregnancy_leave": ["pregnant", "pregnancy", "gravid", "graviditet", "parental", "foreldrepermisjon", "permisjon", "15-9", "fødsel", "adopsjon"],
        "suspension": ["suspensjon", "suspendere", "15-13", "fratre under undersøkelse"],
        "summary_dismissal": ["avskjed", "avskjedige", "immediate", "gross misconduct", "without notice", "15-14", "grovt pliktbrudd"],
        "work_certificate": ["arbeidsattest", "attest", "15-15"],
        "dispute_deadlines": ["forhandling", "forhandlingsmøte", "søksmål", "søksmålsfrist", "17-3", "17-4", "stå i stilling", "tvist"],
        "contract_requirements": ["arbeidsavtale", "kontrakt", "ansettelseskontrakt", "14-5", "14-6", "hva må en kontrakt inneholde"],
        "employee_status": ["oppdragstaker", "arbeidstaker", "konsulent eller ansatt", "1-8", "selvstendig næringsdrivende"],
        "temporary_work": ["midlertidig", "vikar", "vikariat", "14-9", "fast ansettelse", "3-årsregel", "4-årsregel"],
        "working_hours": ["arbeidstid", "alminnelig arbeidstid", "10-4", "hvor mange timer", "skift", "turnus", "pause", "10-9"],
        "overtime": ["overtid", "overtidsarbeid", "10-6", "overtidstillegg", "40 prosent", "pålagt overtid"],
        "holidays": ["ferie", "feriefritid", "ferieloven", "hovedferie", "3 uker", "feriedager", "25 virkedager"],
        "holiday_pay": ["feriepenger", "feriepengeberegning", "10,2 prosent", "12,5 prosent", "sluttoppgjør feriepenger"],
        "whistleblowing": ["varsle", "varsling", "kritikkverdige", "2a-1", "2a-2", "whistleblow"],
        "retaliation": ["gjengjeldelse", "2a-4", "reaksjon på varsling", "straff for å varsle"],
        "harassment": ["trakassering", "psykososialt", "arbeidsmiljø", "4-3", "mobbing", "utilbørlig"],
    }

    matched_intent = next((name for name, terms in topics.items() if any(term in q for term in terms)), None)

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
        "temporary_work": ("midlertidig", "innleie", "vikar", "bemanningsbyrå"),
    }

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


def run_retrieval_workflow(question: str, top_k: int = 4) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    intent = classify_intent(question)
    domain = intent.get("domain") if intent.get("domain") != "unknown" else None
    chunks = retrieve_chunks(question, top_k=top_k, domain=domain)

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

    target_prov = provision_map.get(intent.get("intent"))
    if target_prov and not any(target_prov in c["source_name"] for c in chunks):
        exact_chunk = get_local_source(target_prov)
        if exact_chunk:
            chunks = [exact_chunk] + chunks[:top_k - 1]

    return chunks, {
        "tools": ["classify_employment_question", "retrieve_legal_sources"],
        "intent": intent,
        "retrieved": len(chunks),
        "source_guarantee": target_prov or "none",
    }
