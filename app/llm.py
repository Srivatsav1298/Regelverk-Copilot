import json
import logging
import os
from openai import OpenAI, RateLimitError, APIError
from app.config import LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, REMOTE_MODEL
from app.schemas import AskResponse, CaseAssessmentRequest, CaseAssessmentResponse

logger = logging.getLogger("regelverk-copilot")
_clients = {}
REQUEST_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "900"))


def provider_name() -> str:
    return "ollama" if LLM_PROVIDER == "ollama" else "openrouter"


def _get_client() -> OpenAI:
    name = provider_name()
    if name not in _clients:
        if name == "ollama":
            _clients[name] = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama", timeout=REQUEST_TIMEOUT_SECONDS, max_retries=0)
        else:
            key = os.getenv("OPENROUTER_API_KEY")
            if not key:
                raise RuntimeError("OPENROUTER_API_KEY is not set")
            _clients[name] = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=0)
    return _clients[name]


def _model() -> str:
    return OLLAMA_MODEL if provider_name() == "ollama" else REMOTE_MODEL


def translate_to_norwegian(query: str) -> str:
    glossary = "oppsigelsesfrist, oppsigelse, prøvetid, avskjed, oppsigelsesvern ved sykdom, svangerskap"
    # Avoid a network/model round trip for common supported intents. This also
    # makes retrieval reliable when Ollama is intentionally offline.
    lower_query = query.lower()
    local_terms = {
        "sick leave": "sykefravær oppsigelsesvern ved sykdom § 15-8",
        "sick": "sykefravær oppsigelsesvern ved sykdom § 15-8",
        "illness": "sykdom oppsigelsesvern ved sykdom § 15-8",
        "pregnant": "graviditet oppsigelsesvern ved svangerskap § 15-9",
        "pregnancy": "graviditet oppsigelsesvern ved svangerskap § 15-9",
        "parental leave": "foreldrepermisjon oppsigelsesvern § 15-9",
        "probation": "prøvetid § 15-6",
        "without notice": "avskjed § 15-14",
        "gross misconduct": "grovt pliktbrudd avskjed § 15-14",
        "notice period": "oppsigelsesfrist § 15-3",
        "oppsigelsesfrist": "oppsigelsesfrist § 15-3",
        "valid reason": "saklig begrunnelse § 15-7",
        "specific cause": "saklig begrunnelse § 15-7",
        "saklig": "saklig begrunnelse § 15-7",
    }
    for term, norwegian_terms in local_terms.items():
        if term in lower_query:
            return f"{query} {norwegian_terms}"
    try:
        response = _get_client().chat.completions.create(
            model=_model(),
            messages=[{"role": "system", "content": f"Translate to Norwegian bokmål for employment law retrieval. Use exact terms when relevant: {glossary}. Return only the translation."}, {"role": "user", "content": query}],
            temperature=0,
            max_tokens=120,
        )
        return (response.choices[0].message.content or query).strip()
    except Exception as exc:
        logger.warning("Translation unavailable; using original query (%s)", type(exc).__name__)
        return query


def _safe_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(line for line in cleaned.splitlines() if not line.strip().startswith("```"))
    return json.loads(cleaned)


def _fallback(message: str) -> AskResponse:
    return AskResponse(answer=message, citations=[], confidence="low")


def _first_sentence(text: str) -> str:
    # Legal chunks contain numbered paragraphs; the first complete sentence is
    # enough for a short, auditable fallback citation.
    sentence = text.replace("\n", " ").split(". ", 1)[0].strip()
    return sentence + ("." if sentence and not sentence.endswith(".") else "")


def _deterministic_answer(question: str, chunks: list, language: str) -> AskResponse | None:
    """Answer narrow, well-supported intents without an LLM.

    This is deliberately conservative: it only handles facts represented by an
    explicit provision and returns no answer for anything else.
    """
    q = question.lower()
    target = None
    if any(term in q for term in ("sick leave", "sick", "syk", "sykefravær", "illness")):
        target = "§ 15-8"
        answer = (
            "An employee who is wholly or partly absent because of an accident or illness cannot be dismissed for that reason during the first 12 months after the incapacity began. A dismissal during that protected period is presumed to be because of the sickness unless the employer makes another reason highly probable."
            if language == "en" else
            "En arbeidstaker som er helt eller delvis borte fra arbeidet på grunn av sykdom, kan ikke sies opp av den grunn de første 12 månedene etter at arbeidsuførheten inntrådte. En oppsigelse i verneperioden presumeres å skyldes sykefraværet med mindre arbeidsgiver gjør en annen grunn overveiende sannsynlig."
        )
    elif any(term in q for term in ("pregnant", "pregnancy", "gravid", "parental leave", "foreldrepermisjon", "permisjon")):
        target = "§ 15-9"
        answer = (
            "Pregnancy cannot by itself be used as the reason for dismissal. Employees on qualifying parental leave also have special protection, so the reason, timing, and documentation must be reviewed before any action."
            if language == "en" else
            "Graviditet kan ikke i seg selv brukes som grunnlag for oppsigelse. Arbeidstakere i kvalifisert foreldrepermisjon har også et særskilt vern, så grunnlag, tidspunkt og dokumentasjon må vurderes før arbeidsgiver gjør noe."
        )
    elif any(term in q for term in ("probation", "prøvetid")):
        target = "§ 15-6"
        answer = (
            "During a written probation period, a dismissal must be connected to the employee's adaptation to the work, professional competence, or reliability. The probationary period may normally be up to six months."
            if language == "en" else
            "I en skriftlig avtalt prøvetid må oppsigelsen være begrunnet i arbeidstakerens tilpasning til arbeidet, faglige dyktighet eller pålitelighet. Prøvetiden kan normalt avtales i inntil seks måneder."
        )
    elif any(term in q for term in ("immediate dismissal", "without notice", "gross misconduct", "avskjed")):
        target = "§ 15-14"
        answer = (
            "Immediate dismissal requires gross breach of duty or another material breach of the employment contract. That is a high-risk action and should be reviewed with qualified HR or legal counsel before proceeding."
            if language == "en" else
            "Avskjed med øyeblikkelig fratreden krever grovt pliktbrudd eller annet vesentlig mislighold av arbeidsavtalen. Dette er et høyrisikotiltak som bør kvalitetssikres av kvalifisert HR eller juridisk rådgiver før det gjennomføres."
        )
    elif any(term in q for term in ("notice period", "notice", "oppsigelsesfrist", "how long do i have to give notice", "oppsigelse")):
        target = "§ 15-3"
        answer = (
            "The statutory mutual notice period is normally one month. It increases to at least two months after five years of continuous employment and at least three months after ten years. For employer dismissals after ten years, the minimum is four months after age 50, five months after age 55, and six months after age 60. A written probation period normally has a 14-day notice period."
            if language == "en" else
            "Den lovbestemte gjensidige oppsigelsesfristen er normalt én måned. Den øker til minst to måneder etter fem års sammenhengende ansettelse og minst tre måneder etter ti år. Ved oppsigelse fra arbeidsgiver etter ti år er fristen minst fire måneder etter fylte 50 år, fem måneder etter fylte 55 år og seks måneder etter fylte 60 år. Skriftlig avtalt prøvetid har normalt 14 dagers frist."
        )
    elif any(term in q for term in ("valid reason", "specific cause", "without a reason", "saklig", "saklig begrunnelse", "reason to terminate")):
        target = "§ 15-7"
        answer = (
            "An employee cannot be dismissed without an objectively justified reason connected to the undertaking, the employer, or the employee. In downsizing cases, suitable alternative work and the balance between business need and employee disadvantage must also be considered."
            if language == "en" else
            "En arbeidstaker kan ikke sies opp uten at oppsigelsen er saklig begrunnet i virksomhetens, arbeidsgivers eller arbeidstakerens forhold. Ved nedbemanning må arbeidsgiver også vurdere passende annet arbeid og avveiningen mellom virksomhetens behov og ulempen for arbeidstakeren."
        )
    else:
        return None

    matching = next((chunk for chunk in chunks if target in chunk["source_name"]), None)
    if not matching:
        return None
    return AskResponse(answer=answer, citations=[{"source_name": matching["source_name"], "excerpt": _first_sentence(matching["chunk_text"])}], confidence="high")


def generate_answer(question: str, chunks: list, language: str = "auto", audience: str = "employer") -> AskResponse:
    context = "\n\n".join(f"[{c['source_name']}]\n{c['chunk_text']}" for c in chunks)
    # For narrow, high-risk legal facts, deterministic source-backed answers
    # are safer and faster than asking a model to paraphrase them. The model
    # remains available for compound or explanatory questions.
    deterministic = _deterministic_answer(question, chunks, language)
    if deterministic:
        deterministic.trace = {"fallback": "deterministic_legal_rule", "model_error": "not_used"}
        return deterministic
    requested_language = "Norwegian bokmål" if language == "nb" else "English" if language == "en" else "the user's language"
    prompt = f"""You are Regelverk Copilot, a cautious Norwegian employment-law information assistant for a {audience}. Answer in {requested_language}. Never invent facts. Cite only exact supporting excerpts from the supplied sources. If the sources do not answer the question, say that clearly and use low confidence. Keep the answer practical: what the {audience} should check next. Specific numbers must match the source exactly. Return JSON only with answer, citations (source_name and excerpt), and confidence (high or low).

SOURCES:\n{context}"""
    try:
        response = _get_client().chat.completions.create(
            model=_model(),
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": question}],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        raw = response.choices[0].message.content
        if not raw:
            return _fallback("Jeg klarte ikke å lage et pålitelig svar. Prøv å formulere spørsmålet på nytt.")
        return AskResponse(**_safe_json(raw))
    except (RateLimitError, APIError, RuntimeError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Answer generation failed safely (%s)", type(exc).__name__)
        deterministic = _deterministic_answer(question, chunks, language)
        if deterministic:
            deterministic.trace = {"fallback": "deterministic_legal_rule", "model_error": type(exc).__name__}
            return deterministic
        return _fallback("Jeg kan ikke bekrefte dette spørsmålet mot de støttede kildene. Temaet kan være utenfor Arbeidsmiljøloven kapittel 15 i denne versjonen. Kontroller saken med en kvalifisert rådgiver.")
    except Exception as exc:
        logger.exception("Unexpected model failure: %s", type(exc).__name__)
        deterministic = _deterministic_answer(question, chunks, language)
        return deterministic or _fallback("Jeg kan ikke bekrefte dette på en trygg måte akkurat nå.")


def generate_case_assessment(case: CaseAssessmentRequest, chunks: list, deterministic: dict | None = None) -> CaseAssessmentResponse:
    deterministic = deterministic or {}
    facts = case.model_dump_json(exclude_none=True)
    context = "\n\n".join(f"[{c['source_name']}]\n{c['chunk_text']}" for c in chunks)
    prompt = f"""Assess this Norwegian employment situation using only the supplied legal excerpts and deterministic checks. This is triage, not legal advice. Return JSON with summary, risk_level (low/medium/high/unknown), next_steps (3-5 concrete steps), questions_to_confirm, citations, confidence. Never downgrade a deterministic high/unknown risk. Do not draft a termination notice. Answer in {('English' if case.language == 'en' else 'Norwegian bokmål')}. Case facts: {facts}\nDETERMINISTIC CHECKS: {json.dumps(deterministic, ensure_ascii=False)}\n\nSources:\n{context}"""
    try:
        response = _get_client().chat.completions.create(model=_model(), messages=[{"role":"system", "content": prompt}], temperature=0.1, response_format={"type": "json_object"}, max_tokens=MAX_OUTPUT_TOKENS)
        result = CaseAssessmentResponse(**_safe_json(response.choices[0].message.content or "{}"))
        if deterministic.get("risk", {}).get("level") in {"high", "unknown"}:
            result.risk_level = deterministic["risk"]["level"]
            result.confidence = "low"
        return result
    except Exception as exc:
        logger.warning("Case assessment failed safely (%s)", type(exc).__name__)
        missing = deterministic.get("missing", [])
        next_steps = ["Ikke iverksett oppsigelse eller avskjed før saken er kvalitetssikret.", "Samle arbeidsavtale, fraværsopplysninger og relevant dokumentasjon.", "Avklar saken med HR, tillitsvalgt eller juridisk rådgiver."]
        return CaseAssessmentResponse(summary="Saken kan ikke ferdigstilles uten en tilgjengelig AI-modell. Bruk kontrollpunktene og innhent kvalifisert vurdering.", risk_level=deterministic.get("risk", {}).get("level", "unknown"), next_steps=next_steps, questions_to_confirm=missing or ["Hvilket grunnlag vurderes for tiltaket?"], citations=[], confidence="low")
