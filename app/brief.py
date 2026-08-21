from datetime import datetime, timezone
from html import escape
from uuid import uuid4
from app.source_manifest import corpus_metadata


def render_decision_brief(case, assessment) -> str:
    corpus = corpus_metadata()
    facts = [
        ("Situasjon", case.situation),
        ("Grunnlag", case.termination_reason or "Ikke oppgitt"),
        ("Alder", str(case.employee_age) if case.employee_age is not None else "Ikke oppgitt"),
        ("Ansettelsestid", f"{case.years_employed} år" if case.years_employed is not None else "Ikke oppgitt"),
        ("Prøvetid", "Ja" if case.in_probation else "Nei"),
        ("Sykefravær", "Ja" if case.on_sick_leave else "Nei"),
        ("Graviditet/foreldrepermisjon", "Ja" if case.pregnant_or_parental_leave else "Nei"),
        ("Avskjed vurderes", "Ja" if case.immediate_dismissal else "Nei"),
    ]
    citation_html = "".join(f"<blockquote><strong>{escape(c.source_name)}</strong><br>{escape(c.excerpt)}</blockquote>" for c in assessment.citations) or "<p>Ingen kilde kunne verifiseres for vurderingen.</p>"
    list_html = "".join(f"<li>{escape(item)}</li>" for item in assessment.next_steps)
    questions_html = "".join(f"<li>{escape(item)}</li>" for item in assessment.questions_to_confirm) or "<li>Ingen ekstra kontrollspørsmål registrert.</li>"
    facts_html = "".join(f"<tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>" for label, value in facts)
    warning = "Kilden kan være utdatert — kontroller gjeldende rett." if corpus["freshness_warning"] else "Korpusets ferskhet er innenfor varslingsterskelen."
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    case_id = uuid4().hex[:10]
    return f"""<!doctype html><html lang='nb'><head><meta charset='utf-8'><title>Regelverk Copilot – beslutningsnotat</title><style>body{{font-family:Arial,sans-serif;max-width:850px;margin:40px auto;color:#1f2937;line-height:1.5}}h1,h2{{color:#0f172a}}.meta{{color:#64748b;font-size:13px}}.risk{{padding:14px;border-radius:8px;background:{'#fee2e2' if assessment.risk_level == 'high' else '#fef3c7'};font-weight:bold}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;border-bottom:1px solid #e2e8f0;padding:8px;vertical-align:top}}th{{width:28%;color:#475569}}blockquote{{border-left:3px solid #94a3b8;margin:12px 0;padding:8px 14px;background:#f8fafc}}footer{{border-top:1px solid #e2e8f0;margin-top:30px;padding-top:14px;color:#64748b;font-size:12px}}@media print{{body{{margin:15mm}}button{{display:none}}}}</style></head><body><h1>Beslutningsnotat: avslutning av arbeidsforhold</h1><p class='meta'>Saks-ID: {case_id} · Generert: {generated} · Data lagres ikke av Regelverk Copilot.</p><div class='risk'>Risikonivå: {escape(assessment.risk_level.upper())} · Konfidens: {escape(assessment.confidence)}</div><h2>Oppsummering</h2><p>{escape(assessment.summary)}</p><h2>Fakta oppgitt av arbeidsgiver</h2><table>{facts_html}</table><h2>Anbefalte neste steg</h2><ol>{list_html}</ol><h2>Fakta som må avklares</h2><ul>{questions_html}</ul><h2>Kildegrunnlag</h2>{citation_html}<h2>Datagrunnlag</h2><p>{escape(warning)} Korpusversjon: <strong>{escape(corpus['corpus_version'])}</strong>. Oppdatert: {escape(corpus['publication_or_update_date'])}. <a href='{escape(corpus['source_url'])}'>Kildereferanse</a>.</p><footer>Dette er generell informasjon, ikke juridisk rådgivning. Ikke iverksett oppsigelse eller avskjed uten at saken er vurdert av kvalifisert HR-, tillitsvalgt- eller juridisk rådgiver.</footer></body></html>"""
