"""Versioned source and coverage metadata shown to users and release tooling.

The catalogue is explicit: every supported topic maps to verified, ingested
statutory provisions with official Lovdata references.
"""

from datetime import date
from typing import Any, Dict, List

CORPUS_VERSION = "aml-multi-domain-2026-10"
CORPUS_UPDATED_DATE = date(2024, 7, 1)
CORPUS_INGESTED_DATE = date(2026, 10, 16)
FRESHNESS_WARNING_DAYS = 365

SOURCES: List[Dict[str, Any]] = [
    # Termination and Dismissal (AML Chapter 15 & Chapter 17)
    {"domain": "termination", "provision": "§ 15-1", "title": "Drøfting før beslutning om oppsigelse", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-2", "title": "Informasjon og drøfting ved masseoppsigelser", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-3", "title": "Oppsigelsesfrister", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-4", "title": "Formkrav ved oppsigelse", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-5", "title": "Virkninger av formfeil ved oppsigelse", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-6", "title": "Særlig oppsigelsesvern i prøvetid", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-7", "title": "Vern mot usaklig oppsigelse", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "sickness", "provision": "§ 15-8", "title": "Oppsigelsesvern ved sykdom", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "leave", "provision": "§ 15-9", "title": "Oppsigelsesvern ved svangerskap, fødsel eller adopsjon", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-12", "title": "Virkninger av usaklig oppsigelse (erstatning og ugyldighet)", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-13", "title": "Suspensjon under sakens undersøkelse", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-14", "title": "Avskjed ved grovt pliktbrudd", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "termination", "provision": "§ 15-15", "title": "Arbeidsattest", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_15", "status": "supported"},
    {"domain": "disputes", "provision": "§ 17-3", "title": "Forhandlinger ved tvist om oppsigelse eller avskjed", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_17", "status": "supported"},
    {"domain": "disputes", "provision": "§ 17-4", "title": "Søksmålsfrister ved oppsigelse og avskjed", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_17", "status": "supported"},

    # Employment Contracts & Status (AML Chapter 14 & Chapter 1)
    {"domain": "contracts", "provision": "§ 1-8", "title": "Arbeidstaker og oppdragstaker", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_1", "status": "supported"},
    {"domain": "contracts", "provision": "§ 14-5", "title": "Krav om skriftlig arbeidsavtale", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_14", "status": "supported"},
    {"domain": "contracts", "provision": "§ 14-6", "title": "Minimumskrav til innholdet i den skriftlige arbeidsavtalen", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_14", "status": "supported"},
    {"domain": "contracts", "provision": "§ 14-8", "title": "Endringer i arbeidsforholdet", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_14", "status": "supported"},
    {"domain": "temporary_work", "provision": "§ 14-9", "title": "Fast og midlertidig ansettelse", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_14", "status": "supported"},

    # Working Time & Overtime (AML Chapter 10)
    {"domain": "working_time", "provision": "§ 10-4", "title": "Alminnelig arbeidstid", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_10", "status": "supported"},
    {"domain": "working_time", "provision": "§ 10-6", "title": "Overtid og overtidstillegg", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_10", "status": "supported"},
    {"domain": "working_time", "provision": "§ 10-8", "title": "Daglig og ukentlig arbeidsfri", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_10", "status": "supported"},
    {"domain": "working_time", "provision": "§ 10-9", "title": "Pauser", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_10", "status": "supported"},

    # Holidays & Holiday Pay (Ferieloven)
    {"domain": "holidays", "provision": "Ferieloven § 5", "title": "Feriefritidens lengde", "official_url": "https://lovdata.no/lov/1988-04-29-21", "status": "supported"},
    {"domain": "holidays", "provision": "Ferieloven § 6", "title": "Fastsetting av ferie og drøftingsplikt", "official_url": "https://lovdata.no/lov/1988-04-29-21", "status": "supported"},
    {"domain": "holidays", "provision": "Ferieloven § 10", "title": "Beregning av feriepenger", "official_url": "https://lovdata.no/lov/1988-04-29-21", "status": "supported"},
    {"domain": "holidays", "provision": "Ferieloven § 11", "title": "Utbetaling av feriepenger", "official_url": "https://lovdata.no/lov/1988-04-29-21", "status": "supported"},

    # Workplace Rights & Whistleblowing (AML Chapter 2A & Chapter 4)
    {"domain": "workplace_rights", "provision": "§ 2A-1", "title": "Rett til å varsle om kritikkverdige forhold", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_2A", "status": "supported"},
    {"domain": "workplace_rights", "provision": "§ 2A-2", "title": "Fremgangsmåte ved varsling", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_2A", "status": "supported"},
    {"domain": "workplace_rights", "provision": "§ 2A-4", "title": "Forbud mot gjengjeldelse ved varsling", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_2A", "status": "supported"},
    {"domain": "workplace_rights", "provision": "§ 4-3", "title": "Krav til det psykososiale arbeidsmiljøet og vern mot trakassering", "official_url": "https://lovdata.no/lov/2005-06-17-62/kapittel_4", "status": "supported"},
]

DOMAIN_CATALOG: List[Dict[str, Any]] = [
    {"domain": "termination", "label": "Oppsigelse og avskjed", "status": "supported", "depth": "core", "description": "Drøftingsmøte, grunnlag, vern, formkrav, oppsigelsesfrister, suspensjon og avskjed."},
    {"domain": "contracts", "label": "Arbeidsavtaler og ansettelse", "status": "supported", "depth": "core", "description": "Lovkrav til arbeidsavtale, prøvetid, ansatt vs oppdragstaker og endringer."},
    {"domain": "working_time", "label": "Arbeidstid og overtid", "status": "supported", "depth": "core", "description": "Alminnelig arbeidstid, overtidsgrenser, 40% overtidstillegg, pauser og hvile."},
    {"domain": "holidays", "label": "Ferie og feriepenger", "status": "supported", "depth": "core", "description": "Lovfestet feriefritid, drøfting av ferielister, feriepengegrunnlag og sluttoppgjør."},
    {"domain": "leave", "label": "Permisjon og foreldre", "status": "supported", "depth": "core", "description": "Graviditet, fødsel, adopsjon og særskilt oppsigelsesvern ved permisjon."},
    {"domain": "sickness", "label": "Sykefravær og vern", "status": "supported", "depth": "core", "description": "Sykefravær, 12 måneders oppsigelsesvern og dokumentasjonskrav."},
    {"domain": "workplace_rights", "label": "Varsling og arbeidsmiljø", "status": "supported", "depth": "core", "description": "Retten til å varsle, forbud mot gjengjeldelse og vern mot trakassering."},
    {"domain": "disputes", "label": "Konflikt og søksmålsfrister", "status": "supported", "depth": "core", "description": "Krav om forhandlingsmøte (2 uker), søksmålsfrister (8 uker / 6 mnd) og rett til å stå i stilling."},
    {"domain": "temporary_work", "label": "Midlertidig ansettelse", "status": "supported", "depth": "core", "description": "Vilkår for midlertidig stilling, vikariat og 3/4-årsregelen for fast stilling."},
    {"domain": "pay", "label": "Lønn og lønnstrekk", "status": "planned", "depth": "planned", "description": "Allmenngjort minstelønn, trekk i lønn og sluttoppgjør."},
    {"domain": "equality", "label": "Likestilling og diskriminering", "status": "planned", "depth": "planned", "description": "Likestillings- og diskrimineringsloven, forbud mot forskjellsbehandling."},
    {"domain": "reporting", "label": "Offentlig rapportering", "status": "planned", "depth": "planned", "description": "Masseoppsigelsesmelding til NAV, A-melding og offentlige plikter."},
]

WORKFLOWS: List[Dict[str, Any]] = [
    {"id": "ask", "domain": "all", "label": "Still et spørsmål", "description": "Få et kildebasert svar på norsk eller engelsk med eksakte lovhenvisninger."},
    {"id": "termination", "domain": "termination", "label": "Vurder oppsigelse eller avskjed", "description": "Sjekk saklig grunn, drøftingsmøte, vern, oppsigelsesfrister og neste steg."},
    {"id": "contract_audit", "domain": "contracts", "label": "Kontroller arbeidsavtale", "description": "Sjekk om en kontrakt oppfyller lovens 14 obligatoriske minimumskrav etter § 14-6."},
    {"id": "notice_calc", "domain": "termination", "label": "Beregn oppsigelsesfrist", "description": "Beregn nøyaktig lovbestemt frist og sluttdato basert på ansiennitet og alder."},
    {"id": "overtime_calc", "domain": "working_time", "label": "Sjekk arbeidstid og overtid", "description": "Vurder om arbeidstids- og overtidsgrenser er overskredet samt krav på 40% overtidstillegg."},
    {"id": "holiday_calc", "domain": "holidays", "label": "Beregn feriepenger og feriedager", "description": "Sjekk lovfestet feriefritid (25 dager / 5 uker for 60+) og feriepengesats (10,2% / 12,5%)."},
    {"id": "dispute_prep", "domain": "disputes", "label": "Frister ved uenighet", "description": "Få oversikt over frister for forhandlingsmøte (2 uker) og søksmål (8 uker)."},
]


def corpus_metadata() -> Dict[str, Any]:
    age_days = (date.today() - CORPUS_UPDATED_DATE).days
    return {
        "corpus_version": CORPUS_VERSION,
        "source_url": "https://lovdata.no/lov/2005-06-17-62",
        "publication_or_update_date": CORPUS_UPDATED_DATE.isoformat(),
        "ingested_date": CORPUS_INGESTED_DATE.isoformat(),
        "age_days": age_days,
        "freshness_warning": age_days > FRESHNESS_WARNING_DAYS,
        "freshness_warning_days": FRESHNESS_WARNING_DAYS,
        "sources": SOURCES,
        "domains": DOMAIN_CATALOG,
        "workflows": WORKFLOWS,
        "source_statuses": {
            "supported": "Reviewed, ingested and verifiable in local knowledge engine",
            "under_review": "Available with caution",
            "planned": "Curated source ingestion scheduled",
        },
    }


def topic_catalog() -> List[Dict[str, Any]]:
    return DOMAIN_CATALOG


def freshness_report() -> Dict[str, Any]:
    metadata = corpus_metadata()
    return {
        "corpus_version": metadata["corpus_version"],
        "age_days": metadata["age_days"],
        "freshness_warning": metadata["freshness_warning"],
        "total_provisions": len(SOURCES),
        "release_status": "current" if not metadata["freshness_warning"] else "needs_review",
    }
