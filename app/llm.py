import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from groq import Groq

import json
from app.schemas import AskResponse

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def translate_to_norwegian(query: str) -> str:
    """
    Translates a user query into Norwegian using precise Arbeidsmiljøloven
    (Norwegian employment law) terminology, since generic translation misses
    the exact legal vocabulary our source documents use.
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
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
    )
    return response.choices[0].message.content.strip()

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

CRITICAL ACCURACY RULE: Any specific number (time periods, ages, amounts) in your
answer MUST come directly from the excerpt text, copied exactly. Do not summarize,
round, or infer numbers — if an excerpt says "fire måneder" (four months), your
answer must say four months, not a different number. If you are not certain a
number appears explicitly in the excerpts, omit it rather than guess.

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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content

    try:
        parsed = json.loads(raw)
        return AskResponse(**parsed)
    except Exception as e:
        # If the model returns malformed JSON, fail safely rather than crash
        # the API or silently return garbage.
        print(f"Failed to parse model output: {e}\nRaw output: {raw}")
        return AskResponse(
            answer="I wasn't able to generate a reliable answer for this question. Please try rephrasing it.",
            citations=[],
            confidence="low",
        )