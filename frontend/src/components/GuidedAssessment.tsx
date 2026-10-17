import type { Assessment, CaseInput, Language } from "../types";
import { CitationViewer } from "./CitationViewer";

interface GuidedAssessmentProps {
  caseInput: CaseInput;
  onChangeInput: (key: keyof CaseInput, value: any) => void;
  onSubmit: () => void;
  onClear: () => void;
  onPrintBrief: () => void;
  assessment: Assessment | null;
  busy: boolean;
  language: Language;
}

export function GuidedAssessment({
  caseInput,
  onChangeInput,
  onSubmit,
  onClear,
  onPrintBrief,
  assessment,
  busy,
  language,
}: GuidedAssessmentProps) {
  const t = language === "nb" ? {
    title: "Strukturert saksvurdering",
    subtitle: "Triage av en konkret personalsak. Sjekker lovbestemt vern, frister og risiko.",
    clearDraft: "Tøm utkast",
    situationPlaceholder: "Beskriv situasjonen med egne ord. For eksempel: En medarbeider med 8 års ansiennitet er sykmeldt, og bedriften vurderer nedbemanning...",
    reasonLabel: "Hva er det planlagte tiltaket eller grunnlaget?",
    reasonPlaceholder: "F.eks. driftsinnskrenkning, samarbeidsproblemer, pliktbrudd",
    ageLabel: "Arbeidstakers alder",
    ageHint: "Relevans: Alder over 50/55/60 år gir utvidet oppsigelsesfrist etter 10 års ansiennitet.",
    tenureLabel: "Ansiennitet (år)",
    tenureHint: "Relevans: Fristen øker ved 5 og 10 års sammenhengende ansettelse.",
    noticeDateLabel: "Planlagt dato for skriftlig varsel",
    noticeDateHint: "Relevans: Fristen løper fra 1. dag i påfølgende måned.",
    protectionsTitle: "Spesielle forhold og lovbestemt vern",
    sickLeave: "Ansatt er helt eller delvis sykmeldt (§ 15-8: 12 mnd vern)",
    parentalLeave: "Gravid eller i foreldrepermisjon (§ 15-9: særskilt vern)",
    probation: "Ansettelsen er i avtalt prøvetid (§ 15-6: 14 dager frist)",
    immediate: "Avskjed vurderes (§ 15-14: krever grovt pliktbrudd)",
    startAssessment: "Utfør sakstriage",
    nextSteps: "Anbefalte prosessuelle steg",
    clarifyBeforeActing: "Fakta som må bekreftes før handling",
    riskTitle: "Beregnet risikonivå",
    printBrief: "Skriv ut beslutningsnotat ↗",
    whatHappened: "Hva har skjedd?",
    analyzing: "Analyserer sak og regelverk...",
    summary: "Juridisk oppsummering",
    urgent: " · STOPP OG FÅ JURIDISK KVALITETSSIKRING",
    resultLabel: "Resultat av saksvurdering",
  } : {
    title: "Structured Case Assessment",
    subtitle: "Triage a specific employment situation to verify statutory protections, notice periods, and procedural risks.",
    clearDraft: "Clear Draft",
    situationPlaceholder: "Describe the situation in your own words. For example: An employee with 8 years of service is on sick leave, and the company is downsizing...",
    reasonLabel: "Stated ground or considered measure",
    reasonPlaceholder: "E.g. redundancy, performance, contract breach",
    ageLabel: "Employee age",
    ageHint: "Relevance: Age over 50/55/60 extends statutory notice after 10 years of service.",
    tenureLabel: "Years of service",
    tenureHint: "Relevance: Notice period increases after 5 and 10 continuous years.",
    noticeDateLabel: "Planned delivery date of notice",
    noticeDateHint: "Relevance: Notice runs from the 1st of the following month.",
    protectionsTitle: "Special Circumstances & Statutory Protections",
    sickLeave: "Employee on sick leave (§ 15-8: 12-month protection)",
    parentalLeave: "Pregnant or on parental leave (§ 15-9: special protection)",
    probation: "In agreed probation period (§ 15-6: 14 days notice)",
    immediate: "Summary dismissal considered (§ 15-14: gross breach required)",
    startAssessment: "Run Case Triage",
    nextSteps: "Recommended Procedural Next Steps",
    clarifyBeforeActing: "Facts to Verify Before Acting",
    riskTitle: "Evaluated Risk Level",
    printBrief: "Print Decision Brief ↗",
    whatHappened: "What happened?",
    analyzing: "Analysing the case and legislation...",
    summary: "Legal summary",
    urgent: " · STOP AND OBTAIN LEGAL REVIEW",
    resultLabel: "Case assessment result",
  };

  return (
    <div className="guided-assessment-panel" role="region" aria-label={t.title}>
      <div className="panel-header-row">
        <div>
          <h2>{t.title}</h2>
          <p className="subtitle">{t.subtitle}</p>
        </div>
        <button className="minimal-btn" onClick={onClear} title={t.clearDraft}>
          🗑️ {t.clearDraft}
        </button>
      </div>

      <div className="form-group">
        <label htmlFor="situation-text">
            <strong>1. {t.whatHappened}</strong>
        </label>
        <textarea
          id="situation-text"
          value={caseInput.situation}
          onChange={(e) => onChangeInput("situation", e.target.value)}
          placeholder={t.situationPlaceholder}
          rows={4}
          maxLength={1500}
        />
      </div>

      <div className="fields-grid">
        <div className="field-card">
          <label htmlFor="termination-reason">
            <strong>{t.reasonLabel}</strong>
          </label>
          <input
            id="termination-reason"
            type="text"
            value={caseInput.termination_reason}
            onChange={(e) => onChangeInput("termination_reason", e.target.value)}
            placeholder={t.reasonPlaceholder}
          />
        </div>

        <div className="field-card">
          <label htmlFor="employee-age">
            <strong>{t.ageLabel}</strong>
          </label>
          <input
            id="employee-age"
            type="number"
            min="16"
            max="80"
            value={caseInput.employee_age ?? ""}
            onChange={(e) => onChangeInput("employee_age", e.target.value ? Number(e.target.value) : null)}
            placeholder="F.eks. 52"
          />
          <small className="field-hint">{t.ageHint}</small>
        </div>

        <div className="field-card">
          <label htmlFor="years-employed">
            <strong>{t.tenureLabel}</strong>
          </label>
          <input
            id="years-employed"
            type="number"
            min="0"
            step="0.5"
            value={caseInput.years_employed ?? ""}
            onChange={(e) => onChangeInput("years_employed", e.target.value ? Number(e.target.value) : null)}
            placeholder="F.eks. 6.5"
          />
          <small className="field-hint">{t.tenureHint}</small>
        </div>

        <div className="field-card">
          <label htmlFor="notice-date">
            <strong>{t.noticeDateLabel}</strong>
          </label>
          <input
            id="notice-date"
            type="date"
            value={caseInput.notice_date ?? ""}
            onChange={(e) => onChangeInput("notice_date", e.target.value || null)}
          />
          <small className="field-hint">{t.noticeDateHint}</small>
        </div>
      </div>

      <div className="protections-section">
        <p className="section-label"><strong>{t.protectionsTitle}</strong></p>
        <div className="checkboxes-grid">
          <label className="checkbox-tile">
            <input
              type="checkbox"
              checked={caseInput.on_sick_leave}
              onChange={(e) => onChangeInput("on_sick_leave", e.target.checked)}
            />
            <span>🩺 {t.sickLeave}</span>
          </label>
          <label className="checkbox-tile">
            <input
              type="checkbox"
              checked={caseInput.pregnant_or_parental_leave}
              onChange={(e) => onChangeInput("pregnant_or_parental_leave", e.target.checked)}
            />
            <span>👶 {t.parentalLeave}</span>
          </label>
          <label className="checkbox-tile">
            <input
              type="checkbox"
              checked={caseInput.in_probation}
              onChange={(e) => onChangeInput("in_probation", e.target.checked)}
            />
            <span>⏳ {t.probation}</span>
          </label>
          <label className="checkbox-tile danger">
            <input
              type="checkbox"
              checked={caseInput.immediate_dismissal}
              onChange={(e) => onChangeInput("immediate_dismissal", e.target.checked)}
            />
            <span>⚠️ {t.immediate}</span>
          </label>
        </div>
      </div>

      <button
        className="primary wide-btn"
        onClick={onSubmit}
        disabled={busy || !caseInput.situation.trim()}
      >
        {busy ? t.analyzing : t.startAssessment} ↗
      </button>

      {assessment && (
        <div className="assessment-results-card" role="region" aria-label={t.resultLabel}>
          <div className="assessment-top">
            <div className={`risk-badge ${assessment.risk_level}`}>
              {t.riskTitle}: <strong>{assessment.risk_level.toUpperCase()}</strong>
              {assessment.escalation_level === "urgent" && t.urgent}
            </div>
            <button className="secondary-btn" onClick={onPrintBrief}>
              🖨️ {t.printBrief}
            </button>
          </div>

          <div className="assessment-summary">
            <h3>{t.summary}</h3>
            <p>{assessment.summary}</p>
          </div>

          <div className="two-col-grid">
            <div className="action-col">
              <h4>📋 {t.nextSteps}</h4>
              <ol>
                {assessment.next_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>

            <div className="verify-col">
              <h4>🔍 {t.clarifyBeforeActing}</h4>
              <ul>
                {assessment.questions_to_confirm.map((q, idx) => (
                  <li key={idx}>{q}</li>
                ))}
              </ul>
            </div>
          </div>

          <CitationViewer citations={assessment.citations} language={language} />
        </div>
      )}
    </div>
  );
}
