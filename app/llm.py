import os
import json
import logging
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from openai import OpenAI, RateLimitError, APIError
from app.schemas import AskResponse

logger = logging.getLogger("regelverk-copilot")

load_dotenv()

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client


def translate_to_norwegian(query: str) -> str:
    """
    Translates a user query into Norwegian using precise Arbeidsmiljøloven
    (Norwegian employment law) terminology, since generic translation misses
    the exact legal vocabulary our source documents use.

    Falls back to the original (English) query if translation fails —
    embedding an English query is worse than Norwegian, but far better
    than crashing the whole request.
    """
    try:
        response = _get_client().chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the user's question into Norwegian (bokmål), using precise "
                        "Norwegian employment-law terminology as used in Arbeidsmiljøloven. "
                        "Use these exact terms where relevant:\n"
                        "- notice period → oppsigelsesfrist\n"
                        "- to terminate/dismiss an employee → si opp en arbeidstaker\n"
                        "- termination/notice → oppsigelse\n"
                        "- probation period → prøvetid\n"
                        "- summary dismissal / immediate termination → avskjed\n"
                        "- sick leave protection → oppsigelsesvern ved sykdom\n"
                        "- pregnancy protection → oppsigelsesvern ved svangerskap\n"
                        "- unfair dismissal → usaklig oppsigelse\n\n"
                        "Return ONLY the translated text, nothing else — no quotes, no explanation."
                    )
                },
                {"role": "user", "content": query}
            ],
            temperature=0,
            extra_body={"reasoning": {"exclude": True}},
        )
        content = response.choices[0].message.content
        if content is None:
            logger.warning("Translation returned empty content — falling back to original query")
            return query
        return content.strip()
    except (RateLimitError, APIError) as e:
        logger.warning(f"Translation failed ({e}) — falling back to original query")
        return query
    except RuntimeError as e:
        logger.warning(f"LLM client not configured ({e}) — falling back to original query")
        return query


def generate_answer(question: str, chunks: list) -> AskResponse:
    """
    Given a question and retrieved candidate chunks, generates a structured,
    cited answer. The model is instructed to cite ONLY chunks that genuinely
    support the answer — not all chunks it was shown — since retrieval isn't
    always perfectly ranked (see NOTES.md).
    """
    context_block = "\n\n".join(
        f"[{c['source_name']}]\n{c['chunk_text']}" for c in chunks
    )

    system_prompt = f"""You are a legal information assistant for Norwegian employment law.
You are NOT a lawyer and must never claim to give legal advice.

You will be given a question and several candidate excerpts from Arbeidsmiljøloven.
Some excerpts may NOT actually be relevant — only cite the ones that genuinely
support your answer.

CRITICAL ACCURACY RULE: Specific numbers (time periods, ages, amounts) in your answer
must match the excerpts exactly. However, you must ALWAYS write the answer as a
natural sentence in your own words, in the question's language — never copy an
entire excerpt sentence verbatim as the answer, even if it's the correct language.
The "answer" field must be your own explanation; excerpts belong only in "citations".

IMPORTANT: Always answer in the exact same language the user's question was asked in.

Respond with ONLY valid JSON in exactly this shape, nothing else:
{{
  "answer": "<your answer>",
  "citations": [{{"source_name": "<exact source name from the excerpts>", "excerpt": "<the specific supporting sentence>"}}],
  "confidence": "high" or "low"
}}

Set confidence to "low" if the provided excerpts don't clearly and fully answer the question.
If none of the excerpts are relevant, say so honestly in the answer and set confidence to "low"
with an empty citations list — do NOT invent an answer not grounded in the excerpts.

CANDIDATE EXCERPTS:
{context_block}
"""

    try:
        response = _get_client().chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            extra_body={"reasoning": {"exclude": True}},
        )
    except RuntimeError as e:
        logger.warning(f"LLM client not configured ({e})")
        return AskResponse(
            answer="The assistant is not configured. Please set OPENROUTER_API_KEY.",
            citations=[],
            confidence="low",
        )
    except RateLimitError:
        logger.warning("OpenRouter rate limit hit — returning graceful fallback response")
        return AskResponse(
            answer="The assistant is temporarily at its usage limit. Please try again in a little while.",
            citations=[],
            confidence="low",
        )
    except APIError as e:
        logger.warning(f"OpenRouter API error: {e}")
        return AskResponse(
            answer="Something went wrong reaching the assistant. Please try again.",
            citations=[],
            confidence="low",
        )

    raw = response.choices[0].message.content

    if raw is None:
        # Log the full raw response to understand what the model returned
        try:
            raw_dict = response.model_dump()
            logger.warning(f"Model returned empty content (None). Full response: {json.dumps(raw_dict, default=str, ensure_ascii=False)}")
        except Exception:
            logger.warning("Model returned empty content (None). Could not serialize response.")
        return AskResponse(
            answer="I wasn't able to generate a reliable answer for this question. Please try rephrasing it.",
            citations=[],
            confidence="low",
        )

    # Some models wrap JSON in markdown fences despite response_format
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
        return AskResponse(**parsed)
    except Exception as e:
        # If the model returns malformed JSON, fail safely rather than crash
        # the API or silently return garbage.
        logger.error(f"Failed to parse model output: {e}\nRaw output: {raw}")
        return AskResponse(
            answer="I wasn't able to generate a reliable answer for this question. Please try rephrasing it.",
            citations=[],
            confidence="low",
        )
