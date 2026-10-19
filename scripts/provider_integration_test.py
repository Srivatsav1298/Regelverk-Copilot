"""Run one non-sensitive real-provider generation request.

This command is intentionally opt-in and never prints the response or credentials.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm import _get_client, _model, provider_diagnostics, provider_name


def main() -> int:
    diagnostics = provider_diagnostics()
    if diagnostics.get("reachable") is not True:
        print(json.dumps({"status": "BLOCKED", "provider": provider_name(), "diagnostics": diagnostics}, ensure_ascii=False))
        return 3
    try:
        response = _get_client().chat.completions.create(
            model=_model(),
            messages=[{"role": "user", "content": "Reply with the single word OK."}],
            temperature=0,
            max_tokens=4,
        )
        content = (response.choices[0].message.content or "").strip()
        print(json.dumps({"status": "PASS" if content else "FAIL", "provider": provider_name(), "model": _model(), "response_received": bool(content)}, ensure_ascii=False))
        return 0 if content else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "provider": provider_name(), "model": _model(), "error_type": type(exc).__name__}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
