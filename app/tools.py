"""MCP-shaped tool registry used by the transparent workflow.

The registry is intentionally transport-neutral: the same contracts can be
mounted behind an MCP server or called directly from FastAPI.
"""

TOOLS = [
    {
        "name": "extract_case_facts",
        "description": "Normalize employer-provided termination facts without storing them.",
        "input_schema": {"type": "object", "properties": {"case": {"type": "object"}}, "required": ["case"]},
    },
    {
        "name": "calculate_notice_period",
        "description": "Calculate the statutory employer notice period from tenure, age, and probation status.",
        "input_schema": {"type": "object", "properties": {"years_employed": {"type": "number"}, "employee_age": {"type": "integer"}, "in_probation": {"type": "boolean"}}},
    },
    {
        "name": "detect_protected_situation",
        "description": "Detect sickness, pregnancy, or parental-leave protection flags.",
        "input_schema": {"type": "object", "properties": {"case": {"type": "object"}}, "required": ["case"]},
    },
    {
        "name": "check_missing_information",
        "description": "Identify facts required before an employer should act.",
        "input_schema": {"type": "object", "properties": {"case": {"type": "object"}}, "required": ["case"]},
    },
    {
        "name": "classify_employment_question",
        "description": "Classify a question into an employment-law domain and reviewed coverage status.",
        "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
    },
    {
        "name": "build_decision_brief",
        "description": "Render an ephemeral, print-ready HTML decision brief from a completed assessment.",
        "input_schema": {"type": "object", "properties": {"case": {"type": "object"}, "assessment": {"type": "object"}}, "required": ["case", "assessment"]},
    },
    {
        "name": "retrieve_legal_sources",
        "description": "Retrieve grounded excerpts from the indexed, versioned employment-law corpus.",
        "input_schema": {"type": "object", "properties": {"question": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["question"]},
    },
    {
        "name": "identify_missing_facts",
        "description": "Identify facts that can change the answer before a user acts.",
        "input_schema": {"type": "object", "properties": {"case": {"type": "object"}}, "required": ["case"]},
    },
    {
        "name": "calculate_employment_rule",
        "description": "Run a supported employment-law calculator and return a review-required result.",
        "input_schema": {"type": "object", "properties": {"rule": {"type": "string"}, "inputs": {"type": "object"}}, "required": ["rule"]},
    },
    {
        "name": "check_source_freshness",
        "description": "Report corpus version, review date, and freshness status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "verify_citations",
        "description": "Check that a generated citation is an exact excerpt of a retrieved source.",
        "input_schema": {"type": "object", "properties": {"citations": {"type": "array"}, "sources": {"type": "array"}}, "required": ["citations", "sources"]},
    },
]


def tool_manifest() -> dict:
    return {"name": "regelverk-copilot", "version": "1.0", "tools": TOOLS}
