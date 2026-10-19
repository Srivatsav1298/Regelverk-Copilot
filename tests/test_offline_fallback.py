from app import llm


def test_sick_leave_question_has_grounded_offline_fallback(monkeypatch):
    def unavailable_client():
        raise RuntimeError("Ollama unavailable")

    monkeypatch.setattr(llm, "_get_client", unavailable_client)
    result = llm.generate_answer(
        "Can I fire someone who is on sick leave?",
        [{
            "source_name": "Arbeidsmiljøloven § 15-8 | Oppsigelsesvern ved sykdom",
            "chunk_text": "(1) Arbeidstaker som helt eller delvis er borte fra arbeidet på grunn av ulykke eller sykdom kan ikke av denne grunn sies opp de første 12 månedene etter at arbeidsuførheten inntrådte.",
        }],
        language="en",
    )
    assert "12 months" in result.answer
    assert result.citations[0].source_name.endswith("Oppsigelsesvern ved sykdom")
    assert result.confidence == "high"
    assert result.generation_mode == "deterministic_fallback"
    assert result.trace["fallback"] == "deterministic_legal_rule"


def test_each_supported_provision_has_a_deterministic_answer():
    cases = [
        ("What is the notice period?", "§ 15-3", "notice"),
        ("What happens during probation?", "§ 15-6", "probation"),
        ("Do I need a valid reason to terminate someone?", "§ 15-7", "justified"),
        ("Can I fire someone who is sick?", "§ 15-8", "12 months"),
        ("Can I terminate a pregnant employee?", "§ 15-9", "Pregnancy"),
        ("What counts as gross misconduct for immediate dismissal?", "§ 15-14", "Immediate dismissal"),
    ]
    for question, provision, required_text in cases:
        result = llm.generate_answer(
            question,
            [{"source_name": f"Arbeidsmiljøloven {provision} | source", "chunk_text": "Verified legal source excerpt."}],
            language="en",
        )
        assert required_text.lower() in result.answer.lower(), (question, result.answer)
        assert result.citations[0].source_name.startswith(f"Arbeidsmiljøloven {provision}")
