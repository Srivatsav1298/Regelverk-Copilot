"""Versioned source and coverage metadata shown to users and release tooling.

The catalogue is deliberately explicit: a topic is never presented as supported
until its source material has been reviewed and ingested.
"""

from datetime import date

CORPUS_VERSION = "aml-ch15-2024-07"
CORPUS_UPDATED_DATE = date(2024, 7, 1)
# Fixed in the manifest so the metadata is reproducible between requests.
CORPUS_INGESTED_DATE = date(2026, 8, 20)
FRESHNESS_WARNING_DAYS = 365
SOURCE_URL = "https://lovdata.no/lov/2005-06-17-62/kapittel_15"

SOURCES = [
    {"domain": "termination", "provision": "§ 15-3", "title": "Oppsigelsesfrister", "language": "nb", "status": "supported", "official_url": SOURCE_URL, "effective_date": "2024-07-01", "last_reviewed_date": "2024-07-01", "reviewer_status": "needs_review"},
    {"domain": "termination", "provision": "§ 15-6", "title": "Særlig oppsigelsesvern / prøvetid", "language": "nb", "status": "supported", "official_url": SOURCE_URL, "effective_date": "2024-07-01", "last_reviewed_date": "2024-07-01", "reviewer_status": "needs_review"},
    {"domain": "termination", "provision": "§ 15-7", "title": "Vern mot usaklig oppsigelse", "language": "nb", "status": "supported", "official_url": SOURCE_URL, "effective_date": "2024-07-01", "last_reviewed_date": "2024-07-01", "reviewer_status": "needs_review"},
    {"domain": "sickness", "provision": "§ 15-8", "title": "Oppsigelsesvern ved sykdom", "language": "nb", "status": "supported", "official_url": SOURCE_URL, "effective_date": "2024-07-01", "last_reviewed_date": "2024-07-01", "reviewer_status": "needs_review"},
    {"domain": "leave", "provision": "§ 15-9", "title": "Oppsigelsesvern ved svangerskap, fødsel eller adopsjon", "language": "nb", "status": "supported", "official_url": SOURCE_URL, "effective_date": "2024-07-01", "last_reviewed_date": "2024-07-01", "reviewer_status": "needs_review"},
    {"domain": "termination", "provision": "§ 15-14", "title": "Avskjed", "language": "nb", "status": "supported", "official_url": SOURCE_URL, "effective_date": "2024-07-01", "last_reviewed_date": "2024-07-01", "reviewer_status": "needs_review"},
]

DOMAIN_CATALOG = [
    {"domain": "termination", "label": "Oppsigelse og avskjed", "status": "supported", "depth": "core", "description": "Grunnlag, vern, prosess og frister."},
    {"domain": "contracts", "label": "Arbeidsavtaler og ansettelse", "status": "planned", "depth": "planned", "description": "Ansettelse, kontrakter og prøvetid."},
    {"domain": "working_time", "label": "Arbeidstid og turnus", "status": "planned", "depth": "planned", "description": "Arbeidstid, hvile, turnus og overtid."},
    {"domain": "holidays", "label": "Ferie og feriepenger", "status": "planned", "depth": "planned", "description": "Ferieavvikling, feriepenger og frister."},
    {"domain": "leave", "label": "Permisjon og foreldre", "status": "supported", "depth": "core", "description": "Graviditet, fødsel, adopsjon og foreldrepermisjon."},
    {"domain": "sickness", "label": "Sykefravær og oppfølging", "status": "supported", "depth": "core", "description": "Sykefravær, vern og oppfølging."},
    {"domain": "pay", "label": "Lønn og lønnsplikter", "status": "planned", "depth": "planned", "description": "Lønn, trekk, minstelønn og rapportering."},
    {"domain": "equality", "label": "Likestilling og diskriminering", "status": "planned", "depth": "planned", "description": "Likebehandling, diskriminering og gjengjeldelse."},
    {"domain": "hse", "label": "HMS og arbeidsmiljø", "status": "planned", "depth": "planned", "description": "Fysisk og psykososialt arbeidsmiljø."},
    {"domain": "disputes", "label": "Konflikt og dokumentasjon", "status": "planned", "depth": "planned", "description": "Drøfting, dokumentasjon og uenighet."},
    {"domain": "temporary_work", "label": "Midlertidig arbeid og bemanning", "status": "planned", "depth": "planned", "description": "Midlertidige ansettelser, innleie og bemanning."},
    {"domain": "reporting", "label": "Arbeidsgiverens rapportering", "status": "planned", "depth": "planned", "description": "Offentlige meldinger og arbeidsgiverplikter."},
]

WORKFLOWS = [
    {"id": "ask", "domain": "all", "label": "Still et spørsmål", "description": "Få et kildebasert svar på norsk eller engelsk."},
    {"id": "termination", "domain": "termination", "label": "Vurder oppsigelse", "description": "Sjekk grunnlag, vern, frister og neste steg."},
    {"id": "hiring", "domain": "contracts", "label": "Ansett og lag arbeidsavtale", "description": "Sjekk hvilke opplysninger og avklaringer som mangler."},
    {"id": "schedule", "domain": "working_time", "label": "Sjekk arbeidstid", "description": "Strukturer turnus, hvile og overtidsfakta."},
    {"id": "absence", "domain": "sickness", "label": "Følg opp sykefravær", "description": "Finn relevante fakta og trygg oppfølging."},
    {"id": "holiday", "domain": "holidays", "label": "Planlegg ferie", "description": "Samle datoer, ferieønsker og lønnsopplysninger."},
    {"id": "conflict", "domain": "disputes", "label": "Dokumenter en konflikt", "description": "Lag en nøytral oversikt over hendelser og neste steg."},
]


def corpus_metadata() -> dict:
    age_days = (date.today() - CORPUS_UPDATED_DATE).days
    return {
        "corpus_version": CORPUS_VERSION,
        "source_url": SOURCE_URL,
        "publication_or_update_date": CORPUS_UPDATED_DATE.isoformat(),
        "ingested_date": CORPUS_INGESTED_DATE.isoformat(),
        "age_days": age_days,
        "freshness_warning": age_days > FRESHNESS_WARNING_DAYS,
        "freshness_warning_days": FRESHNESS_WARNING_DAYS,
        "sources": SOURCES,
        "domains": DOMAIN_CATALOG,
        "workflows": WORKFLOWS,
        "source_statuses": {"supported": "Reviewed and available", "under_review": "Available with caution", "planned": "Not yet answerable from the verified corpus"},
    }


def topic_catalog() -> list[dict]:
    return DOMAIN_CATALOG


def freshness_report() -> dict:
    metadata = corpus_metadata()
    return {"corpus_version": metadata["corpus_version"], "age_days": metadata["age_days"], "freshness_warning": metadata["freshness_warning"], "last_reviewed": max(s["last_reviewed_date"] for s in SOURCES), "release_status": "needs_review" if metadata["freshness_warning"] else "current"}
