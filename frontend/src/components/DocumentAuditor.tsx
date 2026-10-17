import { useState } from "react";
import type { Language } from "../types";
import { calculateRule } from "../api";

interface DocumentAuditorProps {
  language: Language;
}

export function DocumentAuditor({ language }: DocumentAuditorProps) {
  const [docType, setDocType] = useState<"contract" | "termination">("contract");
  const [text, setText] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAudit = async () => {
    if (!text.trim()) return;
    setAnalyzing(true);
    setResult(null);

    const lower = text.toLowerCase();

    try {
      if (docType === "contract") {
        // Deterministic clause detection
        const fields = {
          parties: ["arbeidsgiver", "partene", "arbeidstaker", "employer", "parties", "employee"].some((word) => lower.includes(word)),
          workplace: ["arbeidssted", "arbeidsplass", "kontor", "adresse", "workplace", "office", "address"].some((word) => lower.includes(word)),
          role: ["stilling", "tittel", "rolle", "arbeidsoppgaver", "position", "title", "role", "duties"].some((word) => lower.includes(word)),
          start_date: ["tiltredelse", "begynner", "oppstart", "startdato", "start date", "commencement", "begins"].some((word) => lower.includes(word)),
          pay: ["lønn", "månedslønn", "årslønn", "godtgjørelse", "salary", "wages", "compensation", "pay"].some((word) => lower.includes(word)),
          working_time: ["arbeidstid", "timer per uke", "normalarbeidstid", "working hours", "hours per week"].some((word) => lower.includes(word)),
          holiday: ["ferie", "feriepenger", "ferieloven", "holiday", "holiday pay", "annual leave"].some((word) => lower.includes(word)),
          notice: ["oppsigelse", "oppsigelsesfrist", "fratreden", "termination", "notice period", "dismissal"].some((word) => lower.includes(word)),
        };
        const res = await calculateRule("contract_check", fields, language);
        setResult(res.result);
      } else {
        // Termination notice audit
        const contents = {
          written: true,
          personal_or_registered: ["personlig", "rekommandert", "overlevert", "sendt", "hand-delivered", "registered mail"].some((word) => lower.includes(word)),
          negotiation_rights: ["forhandling", "17-3", "to uker", "negotiation", "two weeks"].some((word) => lower.includes(word)),
          lawsuit_rights: ["søksmål", "17-4", "åtte uker", "8 uker", "lawsuit", "eight weeks", "8 weeks"].some((word) => lower.includes(word)),
          stay_in_post_rights: ["fortsette i stillingen", "stå i stilling", "15-11", "remain in the position", "stay in post"].some((word) => lower.includes(word)),
          correct_defendant: ["arbeidsgiver", "saksøkt", "organisasjonsnummer", "employer", "defendant", "company number"].some((word) => lower.includes(word)),
        };
        const res = await calculateRule("notice_form_check", contents, language);
        setResult(res.result);
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const t = language === "nb" ? {
    title: "Dokumentkontroll og klausulrevisjon",
    subtitle: "Lim inn en arbeidskontrakt eller et oppsigelsesbrev for automatisk kontroll mot lovens formkrav.",
    contractType: "Arbeidsavtale (§ 14-6)",
    terminationType: "Oppsigelsesbrev (§ 15-4)",
    placeholder: "Lim inn teksten fra avtalen eller brevet her for umiddelbar formkontroll...",
    auditBtn: "Analyser dokument",
    analyzing: "Kontrollerer klausuler...",
    success: "Dokumentet inneholder alle påkrevde lovbestemte klausuler",
    missing: "Mangler vesentlige lovpålagte klausuler",
    missingContract: "Mangler i henhold til § 14-6:",
    missingTermination: "Mangler i henhold til formkravene i § 15-4:",
    defectNote: "Konsekvens av manglende opplysninger:",
    privacyNotice: "🔒 Konfidensialitetsgaranti: Dokumentteksten behandles lokalt og lagres aldri på server.",
  } : {
    title: "Document Intelligence & Clause Audit",
    subtitle: "Paste an employment contract or termination letter to check against statutory formal requirements.",
    contractType: "Employment Contract (§ 14-6)",
    terminationType: "Termination Letter (§ 15-4)",
    placeholder: "Paste document text here to run instant statutory compliance checks...",
    auditBtn: "Audit Document",
    analyzing: "Checking statutory clauses...",
    success: "Document contains all mandatory statutory clauses",
    missing: "Critical statutory clauses are missing",
    missingContract: "Missing under section 14-6:",
    missingTermination: "Missing under the formal requirements in section 15-4:",
    defectNote: "Consequence of missing information:",
    privacyNotice: "🔒 Privacy guarantee: Text is parsed locally and never stored on the server.",
  };

  return (
    <div className="doc-auditor-panel" role="region" aria-label={t.title}>
      <div className="doc-header">
        <h2>{t.title}</h2>
        <p className="subtitle">{t.subtitle}</p>
      </div>

      <div className="doc-type-toggle">
        <button
          className={`toggle-btn ${docType === "contract" ? "active" : ""}`}
          onClick={() => { setDocType("contract"); setResult(null); }}
        >
          📄 {t.contractType}
        </button>
        <button
          className={`toggle-btn ${docType === "termination" ? "active" : ""}`}
          onClick={() => { setDocType("termination"); setResult(null); }}
        >
          ⚖️ {t.terminationType}
        </button>
      </div>

      <textarea
        className="doc-textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t.placeholder}
        rows={7}
      />

      <div className="doc-footer">
        <span className="privacy-pill">{t.privacyNotice}</span>
        <button
          className="primary"
          onClick={handleAudit}
          disabled={analyzing || !text.trim()}
        >
          {analyzing ? t.analyzing : t.auditBtn} ↗
        </button>
      </div>

      {result && (
        <div className="audit-result-box" role="status">
          <div className={`status-pill ${result.status === "ready_for_review" || result.is_formally_valid ? "good" : "danger"}`}>
            {result.status === "ready_for_review" || result.is_formally_valid
              ? `✓ ${t.success}`
              : `! ${t.missing}`}
          </div>

          {result.missing_clauses?.length > 0 && (
            <div className="missing-list">
              <h4>{t.missingContract}</h4>
              <ul>
                {result.missing_clauses.map((c: string) => <li key={c}>{c}</li>)}
              </ul>
            </div>
          )}

          {result.missing_mandatory_elements?.length > 0 && (
            <div className="missing-list danger">
              <h4>{t.missingTermination}</h4>
              <ul>
                {result.missing_mandatory_elements.map((m: string) => <li key={m}>{m}</li>)}
              </ul>
              <p className="warning-note">
                ⚠️ {t.defectNote} {result.consequence_of_defect}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
