import json
import requests

API_URL = "https://regelverk-copilot.onrender.com/ask"

def load_questions(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def check_answer(question_data, response_json):
    answer_lower = response_json["answer"].lower()
    must_contain = question_data["must_contain"]
    expected_source = question_data["expected_source"]

    if not must_contain and expected_source is None:
        # Out-of-scope question — correct behavior is low confidence, no answer
        passed = response_json["confidence"] == "low"
        reason = "Correctly flagged as out-of-scope" if passed else \
                  "FAILED: should have been low-confidence/out-of-scope"
        return passed, reason

    # In-scope question — check required facts appear
    missing = [kw for kw in must_contain if kw.lower() not in answer_lower]
    facts_ok = len(missing) == 0

    # Check the expected source appears in at least one citation
    source_ok = any(
        expected_source in c["source_name"] for c in response_json["citations"]
    ) if expected_source else True

    passed = facts_ok and source_ok and response_json["confidence"] == "high"

    reasons = []
    if missing:
        reasons.append(f"missing keywords: {missing}")
    if not source_ok:
        reasons.append(f"expected source '{expected_source}' not cited")
    if response_json["confidence"] != "high":
        reasons.append("confidence was not 'high'")

    reason = "All checks passed" if passed else "FAILED: " + "; ".join(reasons)
    return passed, reason


def run_eval(filepath):
    questions = load_questions(filepath)
    results = []

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['question']}")
        response = requests.post(API_URL, json={"question": q["question"]})
        response_json = response.json()

        passed, reason = check_answer(q, response_json)
        results.append({
            "question": q["question"],
            "passed": passed,
            "reason": reason,
            "full_answer": response_json["answer"],
            "full_citations": [c["source_name"] for c in response_json["citations"]],
        })

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} — {reason}\n")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print("=" * 60)
    print(f"RESULT: {passed_count}/{total} passed ({passed_count/total*100:.0f}%)")
    print("=" * 60)

    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\nFailed questions (full detail):")
        for r in failed:
            print(f"\n  Q: {r['question']}")
            print(f"  Reason: {r['reason']}")
            print(f"  Full answer: {r['full_answer']}")
            print(f"  Citations: {r['full_citations']}")


if __name__ == "__main__":
    run_eval("eval/eval_questions.jsonl")