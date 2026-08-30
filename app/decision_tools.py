"""Deterministic, auditable rules used before asking the LLM to explain a case."""

from calendar import monthrange
from datetime import date, timedelta


SUPPORTED_RULES = {"notice_period", "contract_check", "working_time_check", "holiday_check"}


def calculate_notice_period(*, years_employed=None, employee_age=None, in_probation=False, notice_date=None) -> dict:
    if in_probation:
        days = 14
        label = "14 dager"
        provision = "Arbeidsmiljøloven § 15-3 (7)"
    elif years_employed is None:
        return {"status": "unknown", "reason": "Ansettelsestid mangler."}
    elif years_employed < 5:
        days, label, provision = 1, "én måned", "Arbeidsmiljøloven § 15-3 (1)"
    elif years_employed < 10:
        days, label, provision = 2, "to måneder", "Arbeidsmiljøloven § 15-3 (2)"
    elif employee_age is not None and employee_age >= 60:
        days, label, provision = 6, "seks måneder", "Arbeidsmiljøloven § 15-3 (3)"
    elif employee_age is not None and employee_age >= 55:
        days, label, provision = 5, "fem måneder", "Arbeidsmiljøloven § 15-3 (3)"
    elif employee_age is not None and employee_age >= 50:
        days, label, provision = 4, "fire måneder", "Arbeidsmiljøloven § 15-3 (3)"
    else:
        days, label, provision = 3, "tre måneder", "Arbeidsmiljøloven § 15-3 (2)"

    result = {"status": "known", "months_or_days": days, "label": label, "provision": provision}
    if notice_date:
        effective = notice_date + timedelta(days=1)
        if effective.month == 12:
            next_month = effective.replace(year=effective.year + 1, month=1, day=1)
        else:
            next_month = effective.replace(month=effective.month + 1, day=1)
        if in_probation:
            result["period_end"] = (notice_date + timedelta(days=14)).isoformat()
        else:
            month = next_month.month - 1 + days - 1
            year = next_month.year + month // 12
            month = month % 12 + 1
            day = monthrange(year, month)[1]
            result["period_end"] = date(year, month, day).isoformat()
        result["notice_start"] = next_month.isoformat()
    return result


def detect_protected_situation(case) -> dict:
    protections = []
    if case.on_sick_leave:
        protections.append({"type": "sickness", "provision": "§ 15-8", "message": "Sykdom gir et særskilt oppsigelsesvern de første 12 månedene."})
    if case.pregnant_or_parental_leave:
        protections.append({"type": "pregnancy_or_leave", "provision": "§ 15-9", "message": "Graviditet og lovlig foreldrepermisjon krever særskilt kontroll før tiltak."})
    return {"protected": bool(protections), "protections": protections}


def check_missing_information(case) -> list[str]:
    missing = []
    if not case.situation.strip():
        missing.append("Beskriv hva som har skjedd og hvilket tiltak arbeidsgiver vurderer.")
    if case.years_employed is None and not case.in_probation:
        missing.append("Ansettelsestid må avklares for å beregne oppsigelsesfrist.")
    if case.employee_age is None and case.years_employed is not None and case.years_employed >= 10:
        missing.append("Alder må avklares fordi alder over 50 år kan endre fristen ved minst 10 års ansettelse.")
    if not case.termination_reason.strip():
        missing.append("Oppgi om grunnlaget gjelder virksomheten, arbeidsgiver eller arbeidstaker.")
    if case.on_sick_leave and case.pregnant_or_parental_leave:
        missing.append("Avklar hvilket fraværsgrunnlag som gjelder, og ikke bland vernereglene.")
    if case.employee_age is not None and not 14 <= case.employee_age <= 100:
        missing.append("Kontroller at oppgitt alder er realistisk.")
    if case.years_employed is not None and case.years_employed < 0:
        missing.append("Ansettelsestid kan ikke være negativ.")
    return missing


def build_risk(case, missing: list[str], protected: dict) -> dict:
    high_reasons = []
    if protected["protected"]:
        high_reasons.append("særskilt oppsigelsesvern")
    if case.immediate_dismissal:
        high_reasons.append("avskjed eller øyeblikkelig fratreden")
    if not case.termination_reason.strip():
        high_reasons.append("uklart grunnlag")
    if high_reasons:
        return {"level": "high", "reasons": high_reasons, "review_required": True}
    if missing:
        return {"level": "unknown", "reasons": ["vesentlige fakta mangler"], "review_required": True}
    return {"level": "medium", "reasons": ["sjekk saklig grunn, dokumentasjon og drøfting før beslutning"], "review_required": True}


def check_contract_fields(fields: dict) -> dict:
    """A completeness check, not a legal validity decision."""
    required = ["parties", "workplace", "role", "start_date", "pay", "working_time", "holiday", "notice"]
    missing = [name for name in required if not fields.get(name)]
    return {"status": "incomplete" if missing else "ready_for_review", "missing_fields": missing, "review_required": True}


def check_working_time(*, hours_per_week=None, consecutive_days=None, night_work=False) -> dict:
    missing = []
    if hours_per_week is None:
        missing.append("Avtalte timer per uke")
    if consecutive_days is None:
        missing.append("Antall sammenhengende arbeidsdager")
    return {"status": "unknown" if missing else "review_required", "missing": missing, "inputs": {"hours_per_week": hours_per_week, "consecutive_days": consecutive_days, "night_work": night_work}}


def calculate_employment_rule(rule: str, inputs: dict) -> dict:
    if rule == "notice_period":
        return calculate_notice_period(**{k: inputs.get(k) for k in ("years_employed", "employee_age", "in_probation", "notice_date")})
    if rule == "contract_check":
        return check_contract_fields(inputs)
    if rule == "working_time_check":
        return check_working_time(**{k: inputs.get(k) for k in ("hours_per_week", "consecutive_days", "night_work")})
    if rule == "holiday_check":
        return {"status": "needs_source_review", "reason": "Ferie og feriepenger krever en publisert, kontrollert kildeversjon."}
    return {"status": "unsupported", "reason": f"Ukjent regel: {rule}"}
