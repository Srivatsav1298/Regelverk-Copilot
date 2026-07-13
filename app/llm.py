import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from groq import Groq

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