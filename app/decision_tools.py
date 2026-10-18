"""Deterministic, auditable Norwegian labour law rules and calculators.

Used before or in conjunction with AI generation to guarantee exact numbers
and statutory checklists without model hallucination.
"""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

SUPPORTED_RULES = {
    "notice_period",
    "contract_check",
    "working_time_check",
    "holiday_check",
    "holiday_pay_amount",
    "overtime_check",
    "notice_form_check",
    "sick_leave_timeline",
    "droftingsmote_checklist",
    "sluttoppgjor_check",
    "permittering_guide",
    "whistleblowing_routine",
}


def calculate_notice_period(
    *,
    years_employed: Optional[float] = None,
    employee_age: Optional[int] = None,
    in_probation: bool = False,
    notice_date: Optional[date] = None,
) -> dict:
    """Calculates statutory notice period under Arbeidsmiljøloven § 15-3."""
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

    result = {
        "status": "known",
        "months_or_days": days,
        "label": label,
        "provision": provision,
        "employee_resignation_notice": "minst 3 måneder etter 10 år (uavhengig av alder)" if years_employed and years_employed >= 10 else label,
    }

    if notice_date:
        if isinstance(notice_date, str):
            try:
                notice_date = date.fromisoformat(notice_date)
            except Exception:
                notice_date = None
    if notice_date:
        effective = notice_date + timedelta(days=1)
        if in_probation:
            result["notice_start"] = effective.isoformat()
            result["period_end"] = (notice_date + timedelta(days=14)).isoformat()
        else:
            if effective.month == 12:
                next_month = effective.replace(year=effective.year + 1, month=1, day=1)
            else:
                next_month = effective.replace(month=effective.month + 1, day=1)
            month = next_month.month - 1 + days - 1
            year = next_month.year + month // 12
            month = month % 12 + 1
            day = monthrange(year, month)[1]
            result["notice_start"] = next_month.isoformat()
            result["period_end"] = date(year, month, day).isoformat()

    return result


def detect_protected_situation(case) -> dict:
    """Flags statutory special dismissal protection under § 15-8 and § 15-9."""
    protections = []
    if getattr(case, "on_sick_leave", False):
        protections.append({
            "type": "sickness",
            "provision": "Arbeidsmiljøloven § 15-8",
            "message": "Sykdom gir et lovbestemt oppsigelsesvern de første 12 månedene etter arbeidsuførhet inntrådte.",
        })
    if getattr(case, "pregnant_or_parental_leave", False):
        protections.append({
            "type": "pregnancy_or_leave",
            "provision": "Arbeidsmiljøloven § 15-9",
            "message": "Graviditet og lovlig foreldrepermisjon (inntil 1 år) gir særskilt vern mot oppsigelse.",
        })
    return {"protected": bool(protections), "protections": protections}


def check_missing_information(case) -> List[str]:
    """Identifies missing material facts before any employment action."""
    missing = []
    situation = getattr(case, "situation", "")
    if not situation.strip():
        missing.append("Beskriv hva som har skjedd og hvilket tiltak som vurderes.")
    if getattr(case, "years_employed", None) is None and not getattr(case, "in_probation", False):
        missing.append("Ansettelsestid (ansiennitet) må avklares for å beregne oppsigelsesfrist.")
    if getattr(case, "employee_age", None) is None and getattr(case, "years_employed", None) is not None and getattr(case, "years_employed", 0) >= 10:
        missing.append("Alder må avklares fordi alder over 50 år kan gi forlenget oppsigelsesfrist ved minst 10 års ansettelse.")
    if not getattr(case, "termination_reason", "").strip():
        missing.append("Oppgi om grunnlaget gjelder virksomhetens forhold (nedbemanning) eller arbeidstakerens forhold.")
    if getattr(case, "on_sick_leave", False) and getattr(case, "pregnant_or_parental_leave", False):
        missing.append("Avklar hvilket fraværsgrunnlag som er primært, og ikke bland vernebestemmelsene.")
    if getattr(case, "employee_age", None) is not None and not (14 <= case.employee_age <= 100):
        missing.append("Kontroller at oppgitt alder er realistisk.")
    if getattr(case, "years_employed", None) is not None and case.years_employed < 0:
        missing.append("Ansettelsestid kan ikke være negativ.")
    return missing


def build_risk(case, missing: List[str], protected: dict) -> dict:
    high_reasons = []
    if protected.get("protected"):
        high_reasons.append("særskilt oppsigelsesvern (sykdom eller foreldrepermisjon)")
    if getattr(case, "immediate_dismissal", False):
        high_reasons.append("avskjed / øyeblikkelig fratreden krever grovt pliktbrudd (§ 15-14)")
    if not getattr(case, "termination_reason", "").strip():
        high_reasons.append("uklart rettslig grunnlag for oppsigelse")

    if high_reasons:
        return {"level": "high", "reasons": high_reasons, "review_required": True}
    if missing:
        return {"level": "unknown", "reasons": ["vesentlige fakta mangler for sikker vurdering"], "review_required": True}
    return {
        "level": "medium",
        "reasons": ["saklig grunn må dokumenteres og drøftingsmøte (§ 15-1) må gjennomføres før beslutning"],
        "review_required": True,
    }


def check_contract_fields(fields: dict) -> dict:
    """Verifies compliance with the mandatory minimum requirements in AML § 14-6."""
    required = {
        "parties": "Partenes identitet (arbeidsgiver og arbeidstaker)",
        "workplace": "Arbeidsplassen / forretningsadresse",
        "role": "Beskrivelse av arbeidet eller stillingstittel",
        "start_date": "Tidspunkt for arbeidsforholdets begynnelse",
        "pay": "Gjeldende eller avtalt lønn og eventuelle tillegg",
        "working_time": "Normal daglig eller ukentlig arbeidstid",
        "holiday": "Rett til ferie og feriepenger",
        "notice": "Oppsigelsesfrister og opphørsregler",
    }
    missing_keys = [key for key in required if not fields.get(key)]
    missing_clauses = [required[k] for k in missing_keys]
    return {
        "status": "incomplete" if missing_keys else "ready_for_review",
        "missing_fields": missing_keys,
        "missing_clauses": missing_clauses,
        "total_required_core": len(required),
        "present_count": len(required) - len(missing_keys),
        "provision": "Arbeidsmiljøloven § 14-6",
        "review_required": True,
    }


def check_working_time(*, hours_per_week: Optional[float] = None, consecutive_days: Optional[int] = None, night_work: bool = False) -> dict:
    """Checks working time against statutory limits in AML § 10-4 and § 10-8."""
    missing = []
    if hours_per_week is None:
        missing.append("Avtalte timer per uke")
    if consecutive_days is None:
        missing.append("Antall sammenhengende arbeidsdager")

    if missing:
        return {
            "status": "unknown",
            "missing": missing,
            "inputs": {"hours_per_week": hours_per_week, "consecutive_days": consecutive_days, "night_work": night_work},
            "review_required": True,
        }

    violations = []
    warnings = []
    if hours_per_week > 40:
        violations.append(f"Lovens grense for alminnelig ukentlig arbeidstid er 40 timer (§ 10-4). {hours_per_week} timer krever overtidshjemmel.")
    elif night_work and hours_per_week > 38:
        warnings.append("Ved regelmessig natt- eller skiftarbeid er lovgrensen 38 eller 36 timer per uke (§ 10-4 annet ledd).")

    if consecutive_days > 6:
        violations.append(f"Arbeidstaker skal ha en sammenhengende arbeidsfri periode på minst 35 timer i løpet av 7 dager (§ 10-8 annet ledd).")

    return {
        "status": "violation" if violations else ("warning" if warnings else "within_limits"),
        "missing": [],
        "violations": violations,
        "warnings": warnings,
        "provision": "Arbeidsmiljøloven kapittel 10",
        "review_required": True,
    }


def calculate_holiday_details(*, salary_basis: Optional[float] = None, employee_age: Optional[int] = None) -> dict:
    """Calculates statutory holiday entitlement and holiday pay under Ferieloven § 5 og § 10."""
    is_senior = employee_age is not None and employee_age >= 60
    vacation_days = 31 if is_senior else 25
    rate_pct = 12.5 if is_senior else 10.2

    result = {
        "status": "calculated",
        "vacation_days_statutory": vacation_days,
        "vacation_weeks_statutory": "5 uker (inkl. ekstrauke)" if is_senior else "4 uker + 1 dag (25 virkedager)",
        "holiday_pay_rate_pct": rate_pct,
        "provision": "Ferieloven § 5 og § 10",
        "review_required": True,
    }

    if salary_basis is not None and salary_basis > 0:
        amount = round(salary_basis * (rate_pct / 100.0), 2)
        result["estimated_holiday_pay_nok"] = amount

    return result


def calculate_holiday_pay_amount(*, remuneration: object, rate_pct: object) -> dict:
    """Calculate a supplied holiday-pay rate without floating-point money errors."""
    try:
        basis_text = str(remuneration).replace(" ", "").replace("NOK", "")
        if "," in basis_text and len(basis_text.rsplit(",", 1)[1]) == 3:
            basis_text = basis_text.replace(",", "")
        elif "." in basis_text and len(basis_text.rsplit(".", 1)[1]) == 3:
            basis_text = basis_text.replace(".", "")
        else:
            basis_text = basis_text.replace(",", ".")
        basis = Decimal(basis_text)
        rate = Decimal(str(rate_pct).replace("%", "").replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return {"status": "missing_or_invalid", "reason": "Provide a valid remuneration amount and percentage rate."}
    if basis < 0 or rate < 0 or rate > 100:
        return {"status": "missing_or_invalid", "reason": "Remuneration and the percentage rate must be non-negative, and the rate cannot exceed 100%."}
    amount = (basis * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    def money(value: Decimal) -> str:
        return f"{value:,.0f}" if value == value.to_integral() else f"{value:,.2f}"
    return {
        "status": "calculated", "currency": "NOK", "remuneration_nok": float(basis),
        "rate_pct": float(rate), "amount_nok": float(amount),
        "amount_formatted": f"NOK {money(amount)}",
        "formula": f"NOK {money(basis)} × {rate:g}% = NOK {money(amount)}",
        "assumption": "The full supplied amount qualifies as the holiday-pay basis; the legal applicability of the supplied rate is assessed separately.",
    }


def check_termination_notice_form(contents: dict) -> dict:
    """Audits a termination notice against mandatory contents under AML § 15-4."""
    checks = {
        "written": ("Skriftlig form", contents.get("written", False)),
        "personal_or_registered": ("Personlig overlevert eller sendt rekommandert", contents.get("personal_or_registered", False)),
        "negotiation_rights": ("Opplysning om rett til å kreve forhandling innen 2 uker", contents.get("negotiation_rights", False)),
        "lawsuit_rights": ("Opplysning om rett til å reise søksmål innen 8 uker", contents.get("lawsuit_rights", False)),
        "stay_in_post_rights": ("Opplysning om retten til å fortsette i stillingen", contents.get("stay_in_post_rights", False)),
        "correct_defendant": ("Angivelse av hvem som er rett arbeidsgiver og saksøkt", contents.get("correct_defendant", False)),
    }

    missing = [label for key, (label, passed) in checks.items() if not passed]
    is_valid = len(missing) == 0

    return {
        "status": "valid" if is_valid else "defective",
        "is_formally_valid": is_valid,
        "missing_mandatory_elements": missing,
        "consequence_of_defect": "Hvis oppsigelsen mangler disse opplysningene, kan retten kjenne den ugyldig og tilkjenne erstatning etter § 15-5.",
        "provision": "Arbeidsmiljøloven § 15-4 og § 15-5",
        "review_required": True,
    }


def calculate_sick_leave_timeline(
    *,
    first_sick_day: Optional[date] = None,
) -> dict:
    """Calculates the mandatory NAV sick-leave milestone dates and § 15-8 protection window.

    Milestones:
      • Day 1–16  : Employer sick-pay period (Ftrl. § 8-18)
      • Week 4    : Oppfølgingsplan must be written (AML § 4-6 (1))
      • Week 7    : Dialogmøte 1 must be held (AML § 4-6 (2))
      • Week 26   : Dialogmøte 2 – NAV may call it (NAV § 4-6 (3))
      • Week 52   : Maximum sickness benefit period (Ftrl. § 8-12); § 15-8 protection expires
    """
    if first_sick_day is None:
        return {
            "status": "unknown",
            "reason": "Angi sykefraværets første dag for å beregne frister.",
            "review_required": True,
        }
    if isinstance(first_sick_day, str):
        try:
            first_sick_day = date.fromisoformat(first_sick_day)
        except Exception:
            return {"status": "error", "reason": "Ugyldig datoformat. Bruk YYYY-MM-DD.", "review_required": True}

    def _add_weeks(d: date, weeks: int) -> date:
        return d + timedelta(weeks=weeks)

    employer_period_end = first_sick_day + timedelta(days=15)   # days 1–16
    week4_deadline      = _add_weeks(first_sick_day, 4)
    week7_deadline      = _add_weeks(first_sick_day, 7)
    week26_deadline     = _add_weeks(first_sick_day, 26)
    week52_expiry       = _add_weeks(first_sick_day, 52)

    return {
        "status": "calculated",
        "first_sick_day": first_sick_day.isoformat(),
        "milestones": [
            {
                "label": "Arbeidsgiverperiode (dag 1–16)",
                "deadline": employer_period_end.isoformat(),
                "description": "Arbeidsgiver betaler full lønn de første 16 dagene (Ftrl. § 8-18). NAV overtar fra dag 17.",
                "provision": "Folketrygdloven § 8-18",
                "action": "Registrer fraværet i Altinn. Egenmelding gjelder inntil 3 dager (§ 8-24).",
            },
            {
                "label": "Oppfølgingsplan (innen uke 4)",
                "deadline": week4_deadline.isoformat(),
                "description": "Arbeidsgiver og arbeidstaker skal ha utarbeidet en skriftlig oppfølgingsplan innen 4 uker.",
                "provision": "Arbeidsmiljøloven § 4-6 (1)",
                "action": "Lag plan med tilretteleggingstiltak og send til NAV ved behov.",
            },
            {
                "label": "Dialogmøte 1 (innen uke 7)",
                "deadline": week7_deadline.isoformat(),
                "description": "Arbeidsgiver skal kalle inn til dialogmøte senest innen 7 uker ved helt eller delvis fravær.",
                "provision": "Arbeidsmiljøloven § 4-6 (2)",
                "action": "Innkall til møte. Bedriftshelsetjenesten og NAV kan delta.",
            },
            {
                "label": "Dialogmøte 2 – NAV (innen uke 26)",
                "deadline": week26_deadline.isoformat(),
                "description": "NAV skal senest innen 26 uker arrangere dialogmøte 2 dersom arbeidstaker fortsatt er sykmeldt.",
                "provision": "Arbeidsmiljøloven § 4-6 (3)",
                "action": "NAV innkaller. Arbeidsgiver og arbeidstaker møter. Ny handlingsplan utarbeides.",
            },
            {
                "label": "Maks sykepengdperiode / § 15-8-vern utløper (uke 52)",
                "deadline": week52_expiry.isoformat(),
                "description": "Etter 52 ukers sykefravær (ikke nødvendigvis sammenhengende over 3 år) utløper sykepengene og § 15-8-vernet mot oppsigelse.",
                "provision": "Folketrygdloven § 8-12 og Arbeidsmiljøloven § 15-8",
                "action": "Avklar om arbeidstaker kan komme tilbake, og start eventuell nedbemanningsprosess korrekt.",
            },
        ],
        "protection_note": "I hele perioden frem til uke 52 er arbeidstaker vernet mot oppsigelse på grunn av sykdom (§ 15-8). Oppsigelse i verneperioden kan kjennes ugyldig.",
        "review_required": True,
    }


def generate_droftingsmote_checklist(
    *,
    employee_name: str = "[Arbeidstakers navn]",
    position: str = "[Stilling]",
    employer_name: str = "[Arbeidsgiver]",
    reason: str = "virksomhetens forhold",
    notice_date: Optional[date] = None,
) -> dict:
    """Generates a § 15-1 drøftingsmøte protocol checklist and agenda."""
    if notice_date and isinstance(notice_date, str):
        try:
            notice_date = date.fromisoformat(notice_date)
        except Exception:
            notice_date = None

    meeting_deadline = (notice_date - timedelta(days=1)).isoformat() if notice_date else "Før oppsigelse meddeles"

    return {
        "status": "generated",
        "provision": "Arbeidsmiljøloven § 15-1",
        "title": f"Drøftingsmøte – {employee_name} ({position})",
        "employer": employer_name,
        "must_hold_before": meeting_deadline,
        "legal_requirement": "Arbeidsgiver skal så langt det er praktisk mulig drøfte oppsigelse med arbeidstaker og eventuelt tillitsvalgt FØR beslutning tas.",
        "checklist": [
            {"item": "Innkall skriftlig med rimelig varsel (minst 2–3 dager)", "critical": True},
            {"item": f"Opplys om drøftingens tema: {reason}", "critical": True},
            {"item": "Tilby arbeidstaker rett til å ha med tillitsvalgt eller annen rådgiver", "critical": True},
            {"item": "Presenter grunnlaget / fakta for arbeidstaker", "critical": True},
            {"item": "Gi arbeidstaker reell mulighet til å uttale seg og komme med motargumenter", "critical": True},
            {"item": "Nedtegn referat fra møtet og be begge parter signere", "critical": True},
            {"item": "Ta stilling til om andre løsninger er mulige (omplassering, redusert stilling)", "critical": False},
            {"item": "Beslutt etter møtet – ikke under det", "critical": False},
        ],
        "agenda_template": [
            f"1. Åpning og presentasjon av deltakere",
            f"2. Bakgrunn og sakens tema: {reason}",
            f"3. Arbeidstakers syn og eventuelle motargumenter",
            f"4. Vurdering av alternative tiltak (omplassering, tilpasning)",
            f"5. Avslutning – referat underskrives av begge parter",
        ],
        "warning": "Dersom drøftingsmøte ikke gjennomføres, øker risikoen for at oppsigelsen kjennes ugyldig. Det er ikke et absolutt krav, men manglende drøfting tillegges stor vekt i domstolene.",
        "review_required": True,
    }


def calculate_sluttoppgjor(
    *,
    monthly_salary: Optional[float] = None,
    notice_months: Optional[int] = None,
    accrued_holiday_pay_nok: Optional[float] = None,
    salary_basis_holiday: Optional[float] = None,
    employee_age: Optional[int] = None,
    days_owed_vacation: Optional[int] = None,
    outstanding_expenses: Optional[float] = None,
) -> dict:
    """Calculates all components of the final settlement (sluttoppgjør) on termination.

    Covers:
      • Lønn i oppsigelsesperioden (§ 15-3)
      • Feriepenger som ikke er utbetalt (Ferieloven § 11)
      • Eventuell skyldig ferie (virkedager × daglig lønn)
      • Refusjon av utlegg
      • § 14-15 forbud mot lønnstrekk uten lovhjemmel
    """
    components = []
    total = 0.0
    warnings = []

    # 1 – Wages during notice
    if monthly_salary and notice_months:
        notice_pay = round(monthly_salary * notice_months, 2)
        components.append({
            "label": f"Lønn i oppsigelsesperioden ({notice_months} mnd)",
            "amount_nok": notice_pay,
            "provision": "Arbeidsmiljøloven § 15-3",
        })
        total += notice_pay

    # 2 – Holiday pay (if a direct accrued amount is provided)
    if accrued_holiday_pay_nok is not None:
        components.append({
            "label": "Opptjente feriepenger (direkte oppgitt)",
            "amount_nok": round(accrued_holiday_pay_nok, 2),
            "provision": "Ferieloven § 11",
        })
        total += accrued_holiday_pay_nok
    elif salary_basis_holiday is not None:
        is_senior = employee_age is not None and employee_age >= 60
        rate = 0.125 if is_senior else 0.102
        hp = round(salary_basis_holiday * rate, 2)
        components.append({
            "label": f"Opptjente feriepenger ({rate*100:.1f}% av feriepengegrunnlag)",
            "amount_nok": hp,
            "provision": "Ferieloven § 10 og § 11",
        })
        total += hp

    # 3 – Unused vacation days
    if days_owed_vacation and monthly_salary:
        daily_rate = round(monthly_salary * 12 / 260, 2)
        vacation_pay = round(daily_rate * days_owed_vacation, 2)
        components.append({
            "label": f"Avspasering / skyldig ferie ({days_owed_vacation} virkedager à {daily_rate} NOK/dag)",
            "amount_nok": vacation_pay,
            "provision": "Ferieloven § 11 jf. § 5",
        })
        total += vacation_pay

    # 4 – Outstanding expenses
    if outstanding_expenses and outstanding_expenses > 0:
        components.append({
            "label": "Refusjon av utlegg",
            "amount_nok": round(outstanding_expenses, 2),
            "provision": "Arbeidsmiljøloven § 14-15",
        })
        total += outstanding_expenses

    if not components:
        return {
            "status": "insufficient_input",
            "reason": "Oppgi minst månedlig lønn og oppsigelsestid for å beregne sluttoppgjøret.",
            "review_required": True,
        }

    # § 14-15 warnings
    warnings.append("Lønnstrekk er bare tillatt med lovhjemmel eller skriftlig samtykke (§ 14-15). Arbeidsgiver kan IKKE trekke i lønn for ulovlige fravær, eiendomsskade o.l. uten slik hjemmel.")
    warnings.append("Sluttoppgjøret skal utbetales senest ved opphør av ansettelsesforholdet (Ferieloven § 11 annet ledd).")

    return {
        "status": "calculated",
        "components": components,
        "total_nok": round(total, 2),
        "warnings": warnings,
        "provisions": ["Arbeidsmiljøloven § 14-15", "Arbeidsmiljøloven § 15-3", "Ferieloven § 10", "Ferieloven § 11"],
        "review_required": True,
    }


def _add_workdays(start: date, workdays: int) -> date:
    """Return the date after ``workdays`` weekdays, excluding the start date."""
    current = start
    added = 0
    while added < workdays:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def calculate_permittering(
    *,
    notice_date: Optional[date] = None,
    force_majeure: bool = False,
    percentage: Optional[float] = None,
    affected_employees: Optional[int] = None,
) -> dict:
    """Build an auditable permittering timeline based on current NAV guidance.

    Public holidays are intentionally not guessed here; the employer should
    confirm the actual work schedule. NAV counts the employer period in
    arbeidsdager, and part-time permittering can stretch the calendar period.
    """
    if not notice_date:
        return {"status": "unknown", "reason": "Angi datoen permitteringsvarselet gis.", "review_required": True}
    if isinstance(notice_date, str):
        try:
            notice_date = date.fromisoformat(notice_date)
        except Exception:
            return {"status": "error", "reason": "Ugyldig datoformat. Bruk YYYY-MM-DD.", "review_required": True}
    if percentage is not None and not 0 < float(percentage) <= 100:
        return {"status": "error", "reason": "Permitteringsgrad må være mellom 1 og 100 prosent.", "review_required": True}
    notice_days = 2 if force_majeure else 14
    start_date = notice_date + timedelta(days=notice_days)
    # The first permittering day is day 1 of the 15-day employer period.
    wage_period_end = _add_workdays(start_date, 14)
    warnings = [
        "Vurder saklig grunn og dokumenter hvorfor behovet er midlertidig før varsel gis.",
        "Tariffavtale eller Hovedavtalen kan gi andre vilkår enn standardreglene.",
        "Ved delvis permittering må 15 arbeidsdager beregnes etter de timene arbeidstaker faktisk er permittert.",
    ]
    if affected_employees and affected_employees >= 10:
        warnings.append("10 eller flere berørte kan utløse særskilt meldeplikt til NAV – avklar dette før iverksettelse.")
    return {
        "status": "calculated",
        "notice_date": notice_date.isoformat(),
        "notice_period_days": notice_days,
        "permittering_start": start_date.isoformat(),
        "employer_wage_obligation_workdays": 15,
        "employer_wage_obligation_estimated_end": wage_period_end.isoformat(),
        "percentage": percentage,
        "affected_employees": affected_employees,
        "milestones": [
            {"label": "Skriftlig permitteringsvarsel", "date": notice_date.isoformat(), "action": "Oppgi årsak, grad, startdato og forventet varighet."},
            {"label": "Permittering kan iverksettes", "date": start_date.isoformat(), "action": "Registrer faktisk permittering og gi arbeidstaker nødvendig dokumentasjon til NAV."},
            {"label": "Arbeidsgiverperiode 1", "date": wage_period_end.isoformat(), "action": "Arbeidsgiver betaler lønn i 15 arbeidsdager fra første permitteringsdag; kontroller arbeidsplan og fravær."},
        ],
        "checklist": [
            "Dokumenter midlertidig saklig behov og vurder alternative tiltak.",
            "Sjekk tariffavtale, utvelgelseskrets og drøfting med tillitsvalgte.",
            "Bruk skriftlig varsel med permitteringsgrad, årsak, dato og forventet varighet.",
            "Vurder meldeplikt til NAV ved 10 eller flere berørte arbeidstakere.",
            "Informer om registrering som arbeidssøker og søknad om dagpenger.",
        ],
        "provisions": ["Hovedavtalen LO–NHO § 7-2 (der den gjelder)", "NAV: permittering", "Arbeidstilsynet: permittering"],
        "warnings": warnings,
        "review_required": True,
    }


def generate_whistleblowing_routine(*, employer_name: str = "[Virksomhetens navn]", contact: str = "[Kontaktperson / kanal]") -> dict:
    """Generate a minimum written whistleblowing routine for an employer."""
    return {
        "status": "generated",
        "title": f"Rutine for varsling – {employer_name}",
        "employer_name": employer_name,
        "contact": contact,
        "provision": "Arbeidsmiljøloven §§ 2 A-1 til 2 A-6",
        "sections": [
            {"heading": "1. Formål og hvem rutinen gjelder for", "body": f"Rutinen gjelder alle arbeidstakere i {employer_name}, inkludert innleide og tidligere arbeidstakere der loven gjelder. Den skal gjøre det trygt å varsle om kritikkverdige forhold."},
            {"heading": "2. Hva kan det varsles om?", "body": "Det kan varsles om forhold i strid med lov, skriftlige etiske regler eller allment aksepterte etiske normer, for eksempel fare for liv og helse, trakassering, korrupsjon, økonomisk kriminalitet eller brudd på personvern."},
            {"heading": "3. Slik varsler du", "body": f"Varsel kan gis skriftlig eller muntlig til nærmeste leder, verneombud, HR eller {contact}. Beskriv hva som har skjedd, når og hvor, hvem som er involvert, og legg ved dokumentasjon dersom det er trygt."},
            {"heading": "4. Saksbehandling", "body": "Varslet registreres konfidensielt, mottak bekreftes så snart som mulig, og saken undersøkes uten unødig opphold. Den som varsler skal få informasjon om videre behandling så langt taushetsplikt og personvern tillater det."},
            {"heading": "5. Vern mot gjengjeldelse", "body": "Gjengjeldelse mot arbeidstaker som varsler i samsvar med loven er forbudt. Mistanke om gjengjeldelse skal meldes gjennom samme kanaler og undersøkes særskilt."},
            {"heading": "6. Ekstern varsling", "body": "Arbeidstaker kan varsle til offentlig myndighet. Arbeidstilsynet og andre relevante myndigheter kan kontaktes når saken hører under deres ansvarsområde."},
        ],
        "implementation_checklist": ["Tilpass kanaler og ansvarlige personer.", "Forankre rutinen i virksomheten og gjør den lett tilgjengelig.", "Opplær ledere og verneombud i mottak og konfidensiell behandling.", "Revider rutinen ved endringer i organisasjon eller regelverk."],
        "review_required": True,
    }


def _translate_calculation_result(rule: str, result: dict, language: str) -> dict:
    """Translate user-facing deterministic tool text while keeping stable keys."""
    if language != "en":
        return result

    def map_list(values, mapping):
        return [mapping.get(value, value) for value in values]

    if result.get("reason"):
        result["reason"] = {
            "Angi sykefraværets første dag for å beregne frister.": "Enter the first day of sick leave to calculate deadlines.",
            "Ugyldig datoformat. Bruk YYYY-MM-DD.": "Invalid date format. Use YYYY-MM-DD.",
            "Angi datoen permitteringsvarselet gis.": "Enter the date the temporary-layoff notice is given.",
            "Permitteringsgrad må være mellom 1 og 100 prosent.": "The temporary-layoff percentage must be between 1 and 100.",
            "Oppgi minst månedlig lønn og oppsigelsestid for å beregne sluttoppgjøret.": "Provide at least monthly salary and notice period to calculate the final settlement.",
        }.get(result["reason"], result["reason"])

    if rule == "notice_period":
        result["label"] = {"én måned": "one month", "to måneder": "two months", "tre måneder": "three months", "fire måneder": "four months", "fem måneder": "five months", "seks måneder": "six months", "14 dager": "14 days"}.get(result.get("label"), result.get("label"))
        if isinstance(result.get("employee_resignation_notice"), str):
            result["employee_resignation_notice"] = result["employee_resignation_notice"].replace("minst 3 måneder etter 10 år (uavhengig av alder)", "at least 3 months after 10 years (regardless of age)")
    elif rule == "contract_check":
        result["missing_clauses"] = map_list(result.get("missing_clauses", []), {
            "Partenes identitet (arbeidsgiver og arbeidstaker)": "Identity of the parties (employer and employee)", "Arbeidsplassen / forretningsadresse": "Workplace / business address", "Beskrivelse av arbeidet eller stillingstittel": "Description of work or job title", "Tidspunkt for arbeidsforholdets begynnelse": "Employment start date", "Gjeldende eller avtalt lønn og eventuelle tillegg": "Current or agreed pay and allowances", "Normal daglig eller ukentlig arbeidstid": "Normal daily or weekly working hours", "Rett til ferie og feriepenger": "Holiday and holiday-pay rights", "Oppsigelsesfrister og opphørsregler": "Notice periods and termination rules",
        })
    elif rule == "working_time_check":
        result["missing"] = map_list(result.get("missing", []), {"Avtalte timer per uke": "Agreed hours per week", "Antall sammenhengende arbeidsdager": "Number of consecutive working days"})
        result["violations"] = [v.replace("Lovens grense for alminnelig ukentlig arbeidstid er", "The statutory limit for ordinary weekly working hours is").replace("timer krever overtidshjemmel.", "hours requires a lawful overtime basis.").replace("Arbeidstaker skal ha en sammenhengende arbeidsfri periode på minst", "Employees must have an uninterrupted rest period of at least").replace("i løpet av 7 dager", "within 7 days") for v in result.get("violations", [])]
        result["warnings"] = [v.replace("Ved regelmessig natt- eller skiftarbeid er lovgrensen", "For regular night or shift work, the statutory limit is") for v in result.get("warnings", [])]
    elif rule == "holiday_check":
        result["vacation_weeks_statutory"] = "5 weeks (including the extra week)" if result.get("vacation_days_statutory") == 31 else "4 weeks + 1 day (25 weekdays)"
    elif rule == "notice_form_check":
        result["missing_mandatory_elements"] = map_list(result.get("missing_mandatory_elements", []), {"Skriftlig form": "Written form", "Personlig overlevert eller sendt rekommandert": "Hand-delivered or sent by registered mail", "Opplysning om rett til å kreve forhandling innen 2 uker": "Information about the right to demand negotiations within 2 weeks", "Opplysning om rett til å reise søksmål innen 8 uker": "Information about the right to file a lawsuit within 8 weeks", "Opplysning om retten til å fortsette i stillingen": "Information about the right to remain in the position", "Angivelse av hvem som er rett arbeidsgiver og saksøkt": "Correct employer and defendant identified"})
        result["consequence_of_defect"] = "If the notice lacks these details, the court may invalidate it and award compensation under section 15-5."
    elif rule == "sick_leave_timeline":
        translations = [
            ("Employer period (days 1–16)", "The employer pays full wages for the first 16 days (National Insurance Act section 8-18).", "Register the absence in Altinn. Self-certification applies for up to 3 days (section 8-24)."),
            ("Follow-up plan (by week 4)", "The employer and employee must prepare a written follow-up plan within 4 weeks.", "Create a plan with accommodation measures and send it to NAV if needed."),
            ("Dialogue meeting 1 (by week 7)", "The employer must call a dialogue meeting no later than week 7 for full or partial absence.", "Invite the participants. The occupational health service and NAV may attend."),
            ("Dialogue meeting 2 – NAV (by week 26)", "NAV should arrange dialogue meeting 2 by week 26 if the employee remains on sick leave.", "NAV will invite the participants. Agree a new action plan."),
            ("Maximum sick-pay period / section 15-8 protection expires (week 52)", "After 52 weeks of sick leave, sick pay and the section 15-8 dismissal protection expire.", "Clarify whether the employee can return and start any downsizing process correctly."),
        ]
        for milestone, (label, description, action) in zip(result.get("milestones", []), translations):
            milestone["label"], milestone["description"], milestone["action"] = label, description, action
        result["protection_note"] = "Until week 52, the employee is protected from dismissal because of illness (section 15-8). A dismissal during the protection period may be invalid."
    elif rule == "droftingsmote_checklist":
        result["title"] = result.get("title", "").replace("Drøftingsmøte", "Discussion meeting")
        result["must_hold_before"] = result.get("must_hold_before", "").replace("Før oppsigelse meddeles", "Before notice is given")
        result["legal_requirement"] = "The employer should, as far as practically possible, discuss the proposed dismissal with the employee and any union representative BEFORE making a decision."
        result["checklist"] = [{**item, "item": item["item"].replace("Innkall skriftlig med rimelig varsel (minst 2–3 dager)", "Invite in writing with reasonable notice (at least 2–3 days)").replace("Tilby arbeidstaker rett til å ha med tillitsvalgt eller annen rådgiver", "Offer the employee the right to bring a union representative or adviser").replace("Presenter grunnlaget / fakta for arbeidstaker", "Present the grounds and facts to the employee").replace("Gi arbeidstaker reell mulighet til å uttale seg og komme med motargumenter", "Give the employee a genuine opportunity to respond").replace("Nedtegn referat fra møtet og be begge parter signere", "Record the meeting and ask both parties to sign").replace("Ta stilling til om andre løsninger er mulige (omplassering, redusert stilling)", "Consider whether alternatives are possible (reassignment, reduced hours)").replace("Beslutt etter møtet – ikke under det", "Decide after the meeting, not during it")} for item in result.get("checklist", [])]
        result["agenda_template"] = [line.replace("Åpning og presentasjon av deltakere", "Opening and introduction of participants").replace("Bakgrunn og sakens tema", "Background and subject of the matter").replace("Arbeidstakers syn og eventuelle motargumenter", "The employee's view and any counterarguments").replace("Vurdering av alternative tiltak", "Consideration of alternative measures").replace("Avslutning – referat underskrives av begge parter", "Closing – both parties sign the minutes") for line in result.get("agenda_template", [])]
        result["warning"] = "If the discussion meeting is not held, the risk of an invalid dismissal increases. It is not an absolute requirement, but courts attach significant weight to the omission."
    elif rule == "sluttoppgjor_check":
        replacements = {"Lønn i oppsigelsesperioden": "Wages during notice period", "Opptjente feriepenger (direkte oppgitt)": "Accrued holiday pay (amount provided)", "Opptjente feriepenger": "Accrued holiday pay", "Avspasering / skyldig ferie": "Time off / outstanding holiday", "Refusjon av utlegg": "Expense reimbursement"}
        for component in result.get("components", []):
            for no, en in replacements.items():
                if component["label"].startswith(no): component["label"] = component["label"].replace(no, en, 1)
        result["warnings"] = ["Salary deductions are only permitted with statutory authority or written consent (section 14-15).", "The final settlement must be paid no later than the end of employment (Holiday Act section 11)."]
        result["reason"] = "Provide at least monthly salary and notice period to calculate the final settlement." if result.get("reason") else result.get("reason")
    elif rule == "permittering_guide":
        result["milestones"] = [{**m, "label": {"Skriftlig permitteringsvarsel": "Written temporary-layoff notice", "Permittering kan iverksettes": "Temporary layoff may begin", "Arbeidsgiverperiode 1": "Employer wage period 1"}.get(m["label"], m["label"]), "action": {"Oppgi årsak, grad, startdato og forventet varighet.": "State the reason, percentage, start date and expected duration.", "Registrer faktisk permittering og gi arbeidstaker nødvendig dokumentasjon til NAV.": "Register the actual layoff and provide the employee with the documents needed by NAV.", "Arbeidsgiver betaler lønn i 15 arbeidsdager fra første permitteringsdag; kontroller arbeidsplan og fravær.": "The employer pays wages for 15 working days from the first layoff day; check the work schedule and absence."}.get(m["action"], m["action"])} for m in result.get("milestones", [])]
        result["checklist"] = ["Document the temporary business need and consider alternatives.", "Check collective agreements, the selection pool and consultation with union representatives.", "Use written notice stating the percentage, reason, date and expected duration.", "Consider the duty to notify NAV when 10 or more employees are affected.", "Tell employees how to register as jobseekers and apply for benefits."]
        result["warnings"] = ["Document a legitimate temporary need before issuing notice.", "A collective agreement may provide different terms.", "For partial layoffs, calculate the 15 working days based on the hours the employee is actually laid off."]
    elif rule == "whistleblowing_routine":
        result["title"] = result.get("title", "").replace("Rutine for varsling", "Whistleblowing routine")
        english = [
            ("1. Purpose and who this routine applies to", f"This routine applies to all employees of {result.get('employer_name')}, including agency workers and former employees where the law applies. It is intended to make reporting concerns safe."),
            ("2. What can be reported?", "You may report conduct that breaches the law, written ethical rules or generally accepted ethical standards, such as threats to life and health, harassment, corruption, financial crime or privacy breaches."),
            ("3. How to report", f"Reports can be made in writing or orally to your manager, safety representative, HR or {result.get('contact')}. Describe what happened, when and where, who was involved and attach documentation if safe."),
            ("4. Handling reports", "Reports are registered confidentially, receipt is confirmed as soon as possible and the matter is investigated without undue delay. The reporter receives updates where confidentiality and privacy allow."),
            ("5. Protection against retaliation", "Retaliation against an employee who reports in accordance with the law is prohibited. Suspected retaliation should be reported through the same channels and investigated separately."),
            ("6. External reporting", "Employees may report to public authorities. The Norwegian Labour Inspection Authority and other relevant authorities may be contacted where the matter falls within their responsibility."),
        ]
        result["sections"] = [{**section, "heading": heading, "body": body} for section, (heading, body) in zip(result.get("sections", []), english)]
        result["implementation_checklist"] = ["Adapt the reporting channels and responsible people.", "Anchor the routine in the organisation and make it easy to access.", "Train managers and safety representatives in confidential handling.", "Review the routine when the organisation or law changes."]
    return result


def calculate_employment_rule(rule: str, inputs: dict, language: str = "nb") -> dict:
    if rule == "holiday_pay_amount":
        return calculate_holiday_pay_amount(remuneration=inputs.get("remuneration"), rate_pct=inputs.get("rate_pct"))
    if rule == "notice_period":
        return _translate_calculation_result(rule, calculate_notice_period(
            years_employed=inputs.get("years_employed"),
            employee_age=inputs.get("employee_age"),
            in_probation=inputs.get("in_probation", False),
            notice_date=inputs.get("notice_date"),
        ), language)
    if rule == "contract_check":
        return _translate_calculation_result(rule, check_contract_fields(inputs), language)
    if rule == "working_time_check":
        return _translate_calculation_result(rule, check_working_time(
            hours_per_week=inputs.get("hours_per_week"),
            consecutive_days=inputs.get("consecutive_days"),
            night_work=inputs.get("night_work", False),
        ), language)
    if rule == "holiday_check":
        return _translate_calculation_result(rule, calculate_holiday_details(
            salary_basis=inputs.get("salary_basis"),
            employee_age=inputs.get("employee_age"),
        ), language)
    if rule == "notice_form_check":
        return _translate_calculation_result(rule, check_termination_notice_form(inputs), language)
    if rule == "sick_leave_timeline":
        return _translate_calculation_result(rule, calculate_sick_leave_timeline(
            first_sick_day=inputs.get("first_sick_day"),
        ), language)
    if rule == "droftingsmote_checklist":
        return _translate_calculation_result(rule, generate_droftingsmote_checklist(
            employee_name=inputs.get("employee_name", "[Arbeidstakers navn]"),
            position=inputs.get("position", "[Stilling]"),
            employer_name=inputs.get("employer_name", "[Arbeidsgiver]"),
            reason=inputs.get("reason", "virksomhetens forhold"),
            notice_date=inputs.get("notice_date"),
        ), language)
    if rule == "sluttoppgjor_check":
        return _translate_calculation_result(rule, calculate_sluttoppgjor(
            monthly_salary=inputs.get("monthly_salary"),
            notice_months=inputs.get("notice_months"),
            accrued_holiday_pay_nok=inputs.get("accrued_holiday_pay_nok"),
            salary_basis_holiday=inputs.get("salary_basis_holiday"),
            employee_age=inputs.get("employee_age"),
            days_owed_vacation=inputs.get("days_owed_vacation"),
            outstanding_expenses=inputs.get("outstanding_expenses"),
        ), language)
    if rule == "permittering_guide":
        return _translate_calculation_result(rule, calculate_permittering(
            notice_date=inputs.get("notice_date"),
            force_majeure=inputs.get("force_majeure", False),
            percentage=inputs.get("percentage"),
            affected_employees=inputs.get("affected_employees"),
        ), language)
    if rule == "whistleblowing_routine":
        return _translate_calculation_result(rule, generate_whistleblowing_routine(
            employer_name=inputs.get("employer_name", "[Virksomhetens navn]"),
            contact=inputs.get("contact", "[Kontaktperson / kanal]"),
        ), language)
    result = {"status": "unsupported", "reason": f"Unknown rule: {rule}" if language == "en" else f"Ukjent regel: {rule}"}
    return _translate_calculation_result(rule, result, language)
