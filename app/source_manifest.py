"""Version and freshness metadata for the legal corpus shown to users."""

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
    {"domain": "termination", "label": "Oppsigelse og avskjed", "status": "supported"},
    {"domain": "contracts", "label": "Arbeidsavtaler og onboarding", "status": "planned"},
    {"domain": "working_time", "label": "Arbeidstid og turnus", "status": "planned"},
    {"domain": "holidays", "label": "Ferie og feriepenger", "status": "planned"},
    {"domain": "leave", "label": "Permisjon og foreldre", "status": "supported"},
    {"domain": "sickness", "label": "Sykefravær", "status": "supported"},
    {"domain": "pay", "label": "Lønn og grunnleggende plikter", "status": "planned"},
    {"domain": "hse", "label": "HMS og arbeidsmiljø", "status": "planned"},
    {"domain": "disputes", "label": "Uenighet og dokumentasjon", "status": "planned"},
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
    }
