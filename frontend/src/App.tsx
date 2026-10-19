import { useEffect, useMemo, useState } from "react";
import { ask, assess, brief, getTopics, sendCorrection, recordVisit, getFreshness, type ConversationTurn } from "./api";
import type { Answer, Assessment, Audience, CaseInput, Language, Topic, Workflow, ActiveTab } from "./types";
import { CategorySelector } from "./components/CategorySelector";
import { LegalCalculators } from "./components/LegalCalculators";
import { GuidedAssessment } from "./components/GuidedAssessment";
import { DocumentAuditor } from "./components/DocumentAuditor";
import { CitationViewer } from "./components/CitationViewer";
import { QuickStart } from "./components/QuickStart";

const initialCase: CaseInput = {
  situation: "",
  domain: "termination",
  audience: "employer",
  termination_reason: "",
  employee_age: null,
  years_employed: null,
  on_sick_leave: false,
  pregnant_or_parental_leave: false,
  in_probation: false,
  immediate_dismissal: false,
  notice_date: null,
  language: "nb",
};

export default function App() {
  const [language, setLanguage] = useState<Language>(() => (localStorage.getItem("rc-language") as Language) || "nb");
  const [audience, setAudience] = useState<Audience>("employer");
  const [activeTab, setActiveTab] = useState<ActiveTab>("ask");
  const [selectedDomain, setSelectedDomain] = useState<string>("all");
  const [question, setQuestion] = useState("");
  const [caseInput, setCaseInput] = useState<CaseInput>(() => {
    try {
      return JSON.parse(localStorage.getItem("rc-case") || "null") || initialCase;
    } catch {
      return initialCase;
    }
  });
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dark, setDark] = useState(false);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [dailyVisitors, setDailyVisitors] = useState<number | null>(null);
  const [sourceStatus, setSourceStatus] = useState<string | null>(null);
  const [conversationContext, setConversationContext] = useState<ConversationTurn[]>([]);

  useEffect(() => {
    getTopics()
      .then(({ topics: loaded, workflows: loadedWorkflows }) => {
        setTopics(loaded);
        setWorkflows(loadedWorkflows);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    getFreshness().then((response) => setSourceStatus(response.source_monitor?.status ?? null)).catch(() => undefined);
  }, []);

  useEffect(() => {
    const storageKey = "rc-anonymous-visitor-id";
    let visitorId = localStorage.getItem(storageKey);
    if (!visitorId) {
      visitorId = typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `visitor-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      localStorage.setItem(storageKey, visitorId);
    }
    recordVisit(visitorId).then((response) => setDailyVisitors(response.daily_visitors)).catch(() => undefined);
  }, []);

  useEffect(() => {
    localStorage.setItem("rc-language", language);
    document.documentElement.lang = language;
  }, [language]);

  useEffect(() => {
    localStorage.setItem("rc-case", JSON.stringify(caseInput));
  }, [caseInput]);

  const t = useMemo(() => {
    return language === "nb"
      ? {
          brand: "Regelverk",
          tagline: "Norsk arbeidsrett og regelverk — kildebasert, transparent og presist.",
          heroTitle: "Arbeidsrett du kan stole på.",
          heroSubtitle: "Beslutningsstøtte for norske arbeidsgivere og arbeidstakere, forankret direkte i gjeldende lovverk fra Lovdata.",
          askTab: "Still spørsmål",
          assessTab: "Sakstriage",
          toolsTab: "Kalkulatorer",
          docTab: "Dokumentkontroll",
          employer: "Arbeidsgiver",
          employee: "Arbeidstaker",
          askPlaceholder: "Hva lurer du på? F.eks. 'Hvor lang er oppsigelsesfristen etter 6 år?' eller 'Må vi ha drøftingsmøte før oppsigelse?'",
          askBtn: "Finn svar",
          privacyNote: "🔒 Gjestemodus: Ingen saktekst lagres på serveren. Utkast forblir kun i nettleseren din.",
          feedbackHelpful: "Var dette svaret nyttig?",
          yes: "Ja",
          no: "Nei",
          questionLabel: "Ditt spørsmål om arbeidsrett",
          confidenceHigh: "Kildebekreftet svar",
          confidenceReview: "Krever individuell kontroll",
          topicPrefix: "Område",
          clarify: "Forhold som bør avklares:",
          searching: "Søker i lovverket...",
          roleLabel: "Velg rolle",
          eyebrow: "ARBEIDSRETT · JURIDISK BESLUTNINGSSTØTTE",
          trustSources: "Offisielle kilder fra Lovdata",
          trustSourcesBody: "Arbeidsmiljøloven, Ferieloven og tilhørende forskrifter med direkte referanser.",
          trustPrivacy: "Gjestemodus som standard",
          trustPrivacyBody: "Ingen personopplysninger eller sakstekst lagres i database.",
          trustPrecision: "Deterministiske garantier",
          trustPrecisionBody: "Frister, satser og lovbestemte klausuler beregnes uten modell-hallusinering.",
          dailyVisitors: "Besøkende i dag",
          sourceChanged: "Offisiell kilde endret – kvalitetssikring pågår.",
          sourceUnavailable: "Kildestatus kunne ikke bekreftes akkurat nå.",
          disclaimer: "Dette er generell juridisk informasjon basert på gjeldende lovverk, ikke individuell advokatbistand. Ved tvist bør saken kvalitetssikres med advokat, tillitsvalgt eller fagforening.",
          deterministic: "Deterministic, source-grounded check — not generated by the language model",
          unavailable: "Kilde- eller tjenestetilgang er midlertidig utilgjengelig",
        }
      : {
          brand: "Regelverk",
          tagline: "Norwegian employment law made clear, source-grounded and actionable.",
          heroTitle: "Norwegian Labour Law You Can Trust.",
          heroSubtitle: "Objective decision support for employers and employees, grounded directly in official Norwegian statutes.",
          askTab: "Ask Question",
          assessTab: "Case Triage",
          toolsTab: "Calculators",
          docTab: "Document Audit",
          employer: "Employer",
          employee: "Employee",
          askPlaceholder: "What do you need guidance on? E.g. 'What is the notice period after 6 years?' or 'Is a discussion meeting mandatory?'",
          askBtn: "Find Answer",
          privacyNote: "🔒 Guest mode: No case text is stored on the server. Drafts stay solely in your browser.",
          feedbackHelpful: "Was this helpful?",
          yes: "Yes",
          no: "No",
          questionLabel: "Your employment-law question",
          confidenceHigh: "Source-verified answer",
          confidenceReview: "Requires individual review",
          topicPrefix: "Topic",
          clarify: "Points to clarify:",
          searching: "Searching the legislation...",
          roleLabel: "Choose your role",
          eyebrow: "EMPLOYMENT LAW · SOURCE-GROUNDED DECISION SUPPORT",
          trustSources: "Official statutory sources",
          trustSourcesBody: "The Working Environment Act, Holiday Act and related regulations with direct references.",
          trustPrivacy: "Guest mode by default",
          trustPrivacyBody: "No personal data or case text is stored in the database.",
          trustPrecision: "Deterministic checks",
          trustPrecisionBody: "Deadlines, rates and statutory clauses are calculated without model hallucination.",
          dailyVisitors: "Visitors today",
          sourceChanged: "An official source changed — verification is required.",
          sourceUnavailable: "Source freshness could not be confirmed right now.",
          disclaimer: "This is general legal information based on official statutes, not individual legal advice. In case of dispute, verify with a qualified lawyer or union representative.",
          deterministic: "Deterministisk, kildebasert kontroll — ikke generert av språkmodellen",
          unavailable: "Kilde- eller tjenestetilgang er midlertidig utilgjengelig",
        };
  }, [language]);

  const handleAskSubmit = async (query = question) => {
    if (!query.trim()) return;
    setBusy(true);
    setError("");
    setAnswer(null);
    try {
      const res = await ask(query, language, audience, conversationContext);
      setAnswer(res);
      setConversationContext((previous) => [
        ...previous,
        { role: "user" as const, content: query },
        { role: "assistant" as const, content: res.answer },
      ].slice(-8));
    } catch {
      setError(language === "nb" ? "Kunne ikke nå tjenesten. Prøv igjen." : "Could not reach the service. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleAssessmentSubmit = async () => {
    if (!caseInput.situation.trim()) return;
    setBusy(true);
    setError("");
    setAssessment(null);
    try {
      const res = await assess({ ...caseInput, audience, language });
      setAssessment(res);
    } catch {
      setError(language === "nb" ? "Vurderingen kunne ikke fullføres. Prøv igjen." : "Assessment could not be completed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleClearDraft = () => {
    localStorage.removeItem("rc-case");
    setCaseInput(initialCase);
    setAssessment(null);
  };

  const handlePrintBrief = async () => {
    if (!assessment) return;
    const html = await brief(caseInput, assessment);
    const popup = window.open("", "_blank");
    if (popup) {
      popup.document.write(html);
      popup.document.close();
      popup.print();
    }
  };

  const updateCase = (key: keyof CaseInput, val: any) => {
    setCaseInput((prev) => ({ ...prev, [key]: val }));
  };

  const handleSelectCategory = (domain: string, samplePrompt?: string) => {
    setSelectedDomain(domain);
    if (samplePrompt && activeTab === "ask") {
      setQuestion(samplePrompt);
    }
  };

  const handleQuickStart = ({ tab, prompt }: { tab: ActiveTab; prompt?: string }) => {
    setActiveTab(tab);
    if (prompt) setQuestion(prompt);
  };

  return (
    <div className={dark ? "app dark" : "app"}>
      <header className="nav" role="banner">
        <a className="brand" href="/" aria-label="Regelverk Copilot Hjem">
          <span className="brand-mark">§</span>
          <div className="brand-text">
            <span className="brand-name">{t.brand}</span>
            <span className="brand-version">Copilot 2.0</span>
          </div>
        </a>

        <div className="nav-actions">
          <div className="audience-toggle" role="group" aria-label={t.roleLabel}>
            <button
              className={audience === "employer" ? "active" : ""}
              onClick={() => setAudience("employer")}
            >
              💼 {t.employer}
            </button>
            <button
              className={audience === "employee" ? "active" : ""}
              onClick={() => setAudience("employee")}
            >
              👤 {t.employee}
            </button>
          </div>

          <button
            className="minimal-btn"
            onClick={() => setDark(!dark)}
            aria-label={dark ? "Bytt til lyst tema" : "Bytt til mørkt tema"}
          >
            {dark ? "☀️" : "🌙"}
          </button>

          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            aria-label="Språkvelger"
            className="lang-select"
          >
            <option value="nb">Norsk (Bokmål)</option>
            <option value="en">English</option>
          </select>
        </div>
      </header>

      <main className="shell" role="main">
        <section className="hero">
          <p className="eyebrow">{t.eyebrow}</p>
          <h1>{t.heroTitle}</h1>
          <p className="subtitle">{t.heroSubtitle}</p>
        </section>

        <nav className="tab-nav" role="tablist" aria-label="Hovednavigasjon">
          <button
            role="tab"
            aria-selected={activeTab === "ask"}
            className={`tab-btn ${activeTab === "ask" ? "active" : ""}`}
            onClick={() => setActiveTab("ask")}
          >
            💬 {t.askTab}
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "assess"}
            className={`tab-btn ${activeTab === "assess" ? "active" : ""}`}
            onClick={() => setActiveTab("assess")}
          >
            📋 {t.assessTab}
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "tools"}
            className={`tab-btn ${activeTab === "tools" ? "active" : ""}`}
            onClick={() => setActiveTab("tools")}
          >
            🧮 {t.toolsTab}
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "doc"}
            className={`tab-btn ${activeTab === "doc" ? "active" : ""}`}
            onClick={() => setActiveTab("doc")}
          >
            📄 {t.docTab}
          </button>
        </nav>

        {activeTab === "ask" && (
          <div className="tab-content" role="tabpanel">
            <QuickStart audience={audience} language={language} onStart={handleQuickStart} />
            <CategorySelector
              topics={topics}
              selectedDomain={selectedDomain}
              onSelectCategory={handleSelectCategory}
              language={language}
            />

            <section className="panel question-panel">
              <label htmlFor="user-question" className="visually-hidden">
                {t.questionLabel}
              </label>
              <textarea
                id="user-question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleAskSubmit();
                  }
                }}
                placeholder={t.askPlaceholder}
                maxLength={1200}
                rows={3}
              />

              <div className="panel-footer">
                <span className="privacy-text">{t.privacyNote}</span>
                <button
                  className="primary"
                  onClick={() => handleAskSubmit()}
                  disabled={busy || !question.trim()}
                >
                  {busy ? t.searching : t.askBtn} ↗
                </button>
              </div>
            </section>

            {error && (
              <div className="error-alert" role="alert">
                ⚠️ {error}
              </div>
            )}

            {answer && (
              <section className="result-card" role="region" aria-label="Svar på spørsmål">
                <div className="result-header">
                  <div className={`risk-pill ${answer.confidence === "high" ? "good" : "review"}`}>
                    {answer.confidence === "high" ? `✓ ${t.confidenceHigh}` : `! ${t.confidenceReview}`}
                  </div>
                  {answer.domain && (
                    <span className="domain-pill">{t.topicPrefix}: {answer.domain}</span>
                  )}
                </div>
                {answer.generation_mode && answer.generation_mode !== "llm" && (
                  <span className="domain-pill">
                    {answer.generation_mode === "unavailable" ? t.unavailable : t.deterministic}
                  </span>
                )}

                <div className="answer-prose">
                  <p>{answer.answer}</p>
                </div>

                {answer.clarifying_questions && answer.clarifying_questions.length > 0 && (
                  <div className="callout-box">
                    <strong>⚠️ {t.clarify}</strong>
                    <ul>
                      {answer.clarifying_questions.map((q, idx) => (
                        <li key={idx}>{q}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <CitationViewer citations={answer.citations} language={language} />

                <div className="feedback-row">
                  <span>{t.feedbackHelpful}</span>
                  <button className="feedback-btn" onClick={() => sendCorrection({ helpful: true })}>
                    👍 {t.yes}
                  </button>
                  <button className="feedback-btn" onClick={() => sendCorrection({ helpful: false, category: "accuracy" })}>
                    👎 {t.no}
                  </button>
                </div>
              </section>
            )}
          </div>
        )}

        {activeTab === "assess" && (
          <div className="tab-content" role="tabpanel">
            <GuidedAssessment
              caseInput={caseInput}
              onChangeInput={updateCase}
              onSubmit={handleAssessmentSubmit}
              onClear={handleClearDraft}
              onPrintBrief={handlePrintBrief}
              assessment={assessment}
              busy={busy}
              language={language}
            />
          </div>
        )}

        {activeTab === "tools" && (
          <div className="tab-content" role="tabpanel">
            <LegalCalculators language={language} />
          </div>
        )}

        {activeTab === "doc" && (
          <div className="tab-content" role="tabpanel">
            <DocumentAuditor language={language} />
          </div>
        )}

        <section className="trust-features">
          <div className="trust-col">
            <div className="trust-icon">📜</div>
            <strong>{t.trustSources}</strong>
            <p>{t.trustSourcesBody}</p>
          </div>
          <div className="trust-col">
            <div className="trust-icon">🔒</div>
            <strong>{t.trustPrivacy}</strong>
            <p>{t.trustPrivacyBody}</p>
          </div>
          <div className="trust-col">
            <div className="trust-icon">⚖️</div>
            <strong>{t.trustPrecision}</strong>
            <p>{t.trustPrecisionBody}</p>
          </div>
        </section>
      </main>

      <footer className="footer" role="contentinfo">
        <p>{t.disclaimer}</p>
        {dailyVisitors !== null && <p className="daily-visitors" aria-label={`${t.dailyVisitors}: ${dailyVisitors}`}>◉ {t.dailyVisitors}: <strong>{dailyVisitors.toLocaleString(language === "nb" ? "nb-NO" : "en-GB")}</strong></p>}
        {sourceStatus === "changed" && <p className="source-status warning">⚠ {t.sourceChanged}</p>}
        {sourceStatus === "unavailable" && <p className="source-status warning">⚠ {t.sourceUnavailable}</p>}
        <p className="footer-meta">Regelverk Copilot 2.0 · Oppdatert for norsk lovgivning 2026</p>
      </footer>
    </div>
  );
}
