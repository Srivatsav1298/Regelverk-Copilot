import { useState } from "react";
import { calculateRule } from "../api";
import type { Language } from "../types";

interface LegalCalculatorsProps {
  language: Language;
}

type Tool = "notice" | "contract" | "holiday" | "form" | "sick" | "droftingsmote" | "sluttoppgjor" | "permittering" | "varsling";

export function LegalCalculators({ language }: LegalCalculatorsProps) {
  const [activeTool, setActiveTool] = useState<Tool>("sick");

  // ── Notice Period ──────────────────────────────────────────────────────────
  const [yearsEmployed, setYearsEmployed] = useState<number>(3);
  const [age, setAge] = useState<number>(35);
  const [inProbation, setInProbation] = useState(false);
  const [noticeDate, setNoticeDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [noticeResult, setNoticeResult] = useState<any>(null);

  // ── Contract Check ─────────────────────────────────────────────────────────
  const [contractFields, setContractFields] = useState<Record<string, boolean>>({
    parties: true, workplace: true, role: true, start_date: true,
    pay: true, working_time: true, holiday: false, notice: false,
  });
  const [contractResult, setContractResult] = useState<any>(null);

  // ── Holiday ────────────────────────────────────────────────────────────────
  const [salaryBasis, setSalaryBasis] = useState<number>(550000);
  const [holidayAge, setHolidayAge] = useState<number>(35);
  const [holidayResult, setHolidayResult] = useState<any>(null);

  // ── Notice Form ────────────────────────────────────────────────────────────
  const [formChecks, setFormChecks] = useState<Record<string, boolean>>({
    written: true, personal_or_registered: true,
    negotiation_rights: false, lawsuit_rights: false,
    stay_in_post_rights: false, correct_defendant: true,
  });
  const [formResult, setFormResult] = useState<any>(null);

  // ── Sick Leave Timeline ────────────────────────────────────────────────────
  const [firstSickDay, setFirstSickDay] = useState<string>(new Date().toISOString().split("T")[0]);
  const [sickResult, setSickResult] = useState<any>(null);

  // ── Drøftingsmøte Checklist ────────────────────────────────────────────────
  const [drofEmployee, setDrofEmployee] = useState("");
  const [drofPosition, setDrofPosition] = useState("");
  const [drofEmployer, setDrofEmployer] = useState("");
  const [drofReason, setDrofReason] = useState(language === "nb" ? "virksomhetens forhold (nedbemanning)" : "business reasons (redundancy)");
  const [drofNoticeDate, setDrofNoticeDate] = useState<string>("");
  const [drofResult, setDrofResult] = useState<any>(null);

  // ── Sluttoppgjør ───────────────────────────────────────────────────────────
  const [sluttMonthlySalary, setSluttMonthlySalary] = useState<number>(55000);
  const [sluttNoticeMonths, setSluttNoticeMonths] = useState<number>(1);
  const [sluttHolidayBasis, setSluttHolidayBasis] = useState<number>(550000);
  const [sluttAge, setSluttAge] = useState<number>(40);
  const [sluttVacationDays, setSluttVacationDays] = useState<number>(0);
  const [sluttExpenses, setSluttExpenses] = useState<number>(0);
  const [sluttResult, setSluttResult] = useState<any>(null);

  // ── Permittering ──────────────────────────────────────────────────────────
  const [permitteringDate, setPermitteringDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [permitteringForce, setPermitteringForce] = useState(false);
  const [permitteringPercentage, setPermitteringPercentage] = useState<number>(100);
  const [permitteringEmployees, setPermitteringEmployees] = useState<number>(1);
  const [permitteringResult, setPermitteringResult] = useState<any>(null);

  // ── Whistleblowing routine ────────────────────────────────────────────────
  const [varslingEmployer, setVarslingEmployer] = useState("");
  const [varslingContact, setVarslingContact] = useState("");
  const [varslingResult, setVarslingResult] = useState<any>(null);

  const [loading, setLoading] = useState(false);

  const nb = language === "nb";

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleCalculateNotice = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("notice_period", {
        years_employed: yearsEmployed, employee_age: age,
        in_probation: inProbation, notice_date: noticeDate || null,
      }, language);
      setNoticeResult(res.result);
    } finally { setLoading(false); }
  };

  const handleAuditContract = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("contract_check", contractFields, language);
      setContractResult(res.result);
    } finally { setLoading(false); }
  };

  const handleCalculateHoliday = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("holiday_check", {
        salary_basis: salaryBasis, employee_age: holidayAge,
      }, language);
      setHolidayResult(res.result);
    } finally { setLoading(false); }
  };

  const handleCheckForm = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("notice_form_check", formChecks, language);
      setFormResult(res.result);
    } finally { setLoading(false); }
  };

  const handleSickLeave = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("sick_leave_timeline", { first_sick_day: firstSickDay }, language);
      setSickResult(res.result);
    } finally { setLoading(false); }
  };

  const handleDroftingsmote = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("droftingsmote_checklist", {
        employee_name: drofEmployee || undefined,
        position: drofPosition || undefined,
        employer_name: drofEmployer || undefined,
        reason: drofReason || undefined,
        notice_date: drofNoticeDate || undefined,
      }, language);
      setDrofResult(res.result);
    } finally { setLoading(false); }
  };

  const handleSluttoppgjor = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("sluttoppgjor_check", {
        monthly_salary: sluttMonthlySalary,
        notice_months: sluttNoticeMonths,
        salary_basis_holiday: sluttHolidayBasis,
        employee_age: sluttAge,
        days_owed_vacation: sluttVacationDays,
        outstanding_expenses: sluttExpenses,
      }, language);
      setSluttResult(res.result);
    } finally { setLoading(false); }
  };

  const handlePermittering = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("permittering_guide", {
        notice_date: permitteringDate,
        force_majeure: permitteringForce,
        percentage: permitteringPercentage,
        affected_employees: permitteringEmployees,
      }, language);
      setPermitteringResult(res.result);
    } finally { setLoading(false); }
  };

  const handleVarsling = async () => {
    setLoading(true);
    try {
      const res = await calculateRule("whistleblowing_routine", {
        employer_name: varslingEmployer || undefined,
        contact: varslingContact || undefined,
      }, language);
      setVarslingResult(res.result);
    } finally { setLoading(false); }
  };

  const tools: { id: Tool; icon: string; label: string; hot?: boolean }[] = [
    { id: "sick",         icon: "🏥", label: nb ? "Sykefravær" : "Sick Leave", hot: true },
    { id: "droftingsmote",icon: "🤝", label: nb ? "Drøftingsmøte" : "Dismissal Meeting", hot: true },
    { id: "sluttoppgjor", icon: "💰", label: nb ? "Sluttoppgjør" : "Final Settlement", hot: true },
    { id: "permittering", icon: "🚧", label: nb ? "Permittering" : "Layoff Guide", hot: true },
    { id: "varsling", icon: "🛡️", label: nb ? "Varslingsrutine" : "Whistleblowing", hot: true },
    { id: "notice",       icon: "⏱️", label: nb ? "Oppsigelsesfrist" : "Notice Period" },
    { id: "contract",     icon: "📄", label: nb ? "Avtalesjekk" : "Contract Audit" },
    { id: "holiday",      icon: "🏖️", label: nb ? "Ferie & lønn" : "Holiday Pay" },
    { id: "form",         icon: "⚖️", label: nb ? "Formkrav" : "Form Check" },
  ];

  const fmtDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString(nb ? "nb-NO" : "en-GB", { day: "2-digit", month: "long", year: "numeric" });
    } catch { return iso; }
  };

  return (
    <div className="calculators-container" role="region" aria-label={nb ? "Juridiske verktøy" : "Legal Tools"}>
      <div className="calc-header">
        <h2>{nb ? "Juridiske kontrollverktøy og beregninger" : "Legal Decision & Calculation Tools"}</h2>
        <p className="subtitle">{nb ? "Deterministiske, lovbestemte sjekker uten modell-usikkerhet." : "Deterministic statutory checks backed by exact legal formulas."}</p>
      </div>

      {/* ── Tab strip ─────────────────────────────────────────────────────── */}
      <div className="calc-tabs" role="tablist">
        {tools.map(({ id, icon, label, hot }) => (
          <button
            key={id}
            role="tab"
            aria-selected={activeTool === id}
            className={`calc-tab ${activeTool === id ? "active" : ""} ${hot ? "calc-tab-hot" : ""}`}
            onClick={() => setActiveTool(id)}
          >
            {icon} {label}{hot && <span className="hot-badge">NY</span>}
          </button>
        ))}
      </div>

      <div className="calc-body">

        {activeTool === "permittering" && (
          <div className="calc-tool">
            <h3>{nb ? "Permitteringsveileder – frister og sjekkliste" : "Temporary Layoff Guide – deadlines and checklist"}</h3>
            <p className="meta">{nb ? "Få en konkret tidslinje for varsel, iverksettelse og arbeidsgivers 15 arbeidsdager med lønnsplikt. Kontroller alltid tariffavtale og NAV før beslutning." : "Get a concrete timeline for notice, start and the employer's 15 working-day wage obligation. Always verify collective agreements and NAV before acting."}</p>
            <div className="calc-grid">
              <label>{nb ? "Dato varsel gis" : "Notice date"}<input type="date" value={permitteringDate} onChange={e => setPermitteringDate(e.target.value)} /></label>
              <label>{nb ? "Permitteringsgrad (%)" : "Layoff percentage (%)"}<input type="number" min="1" max="100" value={permitteringPercentage} onChange={e => setPermitteringPercentage(Number(e.target.value))} /></label>
              <label>{nb ? "Antall berørte arbeidstakere" : "Affected employees"}<input type="number" min="1" value={permitteringEmployees} onChange={e => setPermitteringEmployees(Number(e.target.value))} /></label>
              <label className="checkbox-label"><input type="checkbox" checked={permitteringForce} onChange={e => setPermitteringForce(e.target.checked)} />{nb ? "Uforutsett hendelse (2 dagers varsel)" : "Force majeure (2-day notice)"}</label>
            </div>
            <button className="primary" onClick={handlePermittering} disabled={loading}>{loading ? "..." : (nb ? "Beregn permittering" : "Calculate layoff plan")} ↗</button>
            {permitteringResult?.status === "calculated" && <div className="calc-result" role="status">
              <div className="result-badge info">📅 {nb ? "Permittering kan iverksettes:" : "Layoff may start:"} {fmtDate(permitteringResult.permittering_start)}</div>
              <div className="timeline-grid">{permitteringResult.milestones.map((m: any, i: number) => <div className="timeline-card timeline-card-info" key={i}><strong>{m.label}</strong><span className="timeline-date">📅 {fmtDate(m.date)}</span><p>{m.action}</p></div>)}</div>
              <h4>{nb ? "Før du sender varselet" : "Before sending the notice"}</h4><ul>{permitteringResult.checklist.map((item: string) => <li key={item}>{item}</li>)}</ul>
              <div className="warning-banner">⚠️ {permitteringResult.warnings.join(" ")}</div>
            </div>}
          </div>
        )}

        {activeTool === "varsling" && (
          <div className="calc-tool">
            <h3>{nb ? "Generator for lovpålagt varslingsrutine (§§ 2 A-1–2 A-6)" : "Written Whistleblowing Routine Generator (§§ 2 A-1–2 A-6)"}</h3>
            <p className="meta">{nb ? "Lag et tilpasset førsteutkast som kan forankres og publiseres internt. En rutine må være tilgjengelig og tilpasset virksomheten." : "Create a tailored first draft to approve and publish internally. A routine must be accessible and adapted to the business."}</p>
            <div className="calc-grid"><label>{nb ? "Virksomhet" : "Business name"}<input value={varslingEmployer} onChange={e => setVarslingEmployer(e.target.value)} placeholder="Acme AS" /></label><label>{nb ? "Varslingskanal / kontakt" : "Reporting channel / contact"}<input value={varslingContact} onChange={e => setVarslingContact(e.target.value)} placeholder="HR eller varsel@acme.no" /></label></div>
            <button className="primary" onClick={handleVarsling} disabled={loading}>{loading ? "..." : (nb ? "Generer rutine" : "Generate routine")} ↗</button>
            {varslingResult?.status === "generated" && <div className="calc-result" role="status"><div className="result-badge success">✓ {varslingResult.title}</div>{varslingResult.sections.map((section: any) => <div className="legal-req-box" key={section.heading}><strong>{section.heading}</strong><p>{section.body}</p></div>)}<h4>{nb ? "Implementering" : "Implementation"}</h4><ul>{varslingResult.implementation_checklist.map((item: string) => <li key={item}>{item}</li>)}</ul><div className="warning-banner">⚠️ {nb ? "Tilpass ansvar, kanaler og personvern før publisering. Dette er et utkast, ikke en ferdig juridisk kvalitetssikring." : "Adapt owners, channels and privacy handling before publishing. This is a draft, not final legal review."}</div></div>}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            1. SICK LEAVE TIMELINE
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "sick" && (
          <div className="calc-tool">
            <h3>{nb ? "Sykefravær & NAV-tidslinje (§ 4-6 / § 8-18 / § 15-8)" : "Sick Leave & NAV Timeline Calculator"}</h3>
            <p className="meta">
              {nb
                ? "Beregner alle lovpålagte frister fra første fraværsdag: arbeidsgiverperiode (16 dager), oppfølgingsplan (4 uker), dialogmøte 1 (7 uker), dialogmøte 2 (26 uker) og § 15-8-vernets utløp (52 uker)."
                : "Calculates all statutory deadlines from day 1 of absence: employer period (16 days), follow-up plan (4 wks), dialogue meeting 1 (7 wks), DM2 (26 wks), and § 15-8 protection expiry (52 wks)."}
            </p>
            <div className="calc-grid">
              <label>
                {nb ? "Første sykedag" : "First day of sick leave"}
                <input
                  type="date"
                  value={firstSickDay}
                  onChange={(e) => setFirstSickDay(e.target.value)}
                />
              </label>
            </div>
            <button className="primary" onClick={handleSickLeave} disabled={loading}>
              {loading ? "..." : (nb ? "Beregn frister" : "Calculate deadlines")} ↗
            </button>

            {sickResult?.status === "calculated" && (
              <div className="calc-result sick-timeline" role="status">
                <div className="result-badge success">
                  ✓ {nb ? "Fraværstidslinje fra" : "Timeline from"} {fmtDate(sickResult.first_sick_day)}
                </div>

                <div className="timeline-grid">
                  {sickResult.milestones.map((m: any, i: number) => (
                    <div key={i} className={`timeline-card ${i === 4 ? "timeline-card-danger" : i >= 2 ? "timeline-card-warn" : "timeline-card-info"}`}>
                      <div className="timeline-step">{i + 1}</div>
                      <div className="timeline-content">
                        <strong>{m.label}</strong>
                        <span className="timeline-date">📅 {fmtDate(m.deadline)}</span>
                        <p>{m.description}</p>
                        <div className="timeline-action">
                          <span className="action-pill">👉 {m.action}</span>
                        </div>
                        <code className="provision-tag">{m.provision}</code>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="protection-banner">
                  🛡️ <strong>{nb ? "Vern:" : "Protection:"}</strong> {sickResult.protection_note}
                </div>
              </div>
            )}
            {sickResult?.status === "unknown" && (
              <div className="calc-result"><div className="result-badge warning">⚠ {sickResult.reason}</div></div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            2. DRØFTINGSMØTE CHECKLIST
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "droftingsmote" && (
          <div className="calc-tool">
            <h3>{nb ? "Drøftingsmøte-protokoll & sjekkliste (§ 15-1)" : "Dismissal Discussion Meeting Protocol (§ 15-1)"}</h3>
            <p className="meta">
              {nb
                ? "Arbeidsgiver skal så langt det er praktisk mulig drøfte oppsigelse med arbeidstaker FØR beslutningen tas. Manglende drøfting øker risikoen for ugyldig oppsigelse betraktelig."
                : "The employer must as far as practically possible discuss the dismissal with the employee BEFORE a decision is made. Failing to do so significantly increases the risk of an invalid termination."}
            </p>
            <div className="calc-grid calc-grid-4">
              <label>
                {nb ? "Arbeidstakers navn (valgfritt)" : "Employee name (optional)"}
                <input type="text" value={drofEmployee} onChange={e => setDrofEmployee(e.target.value)} placeholder={nb ? "Ola Nordmann" : "John Smith"} />
              </label>
              <label>
                {nb ? "Stilling" : "Position"}
                <input type="text" value={drofPosition} onChange={e => setDrofPosition(e.target.value)} placeholder={nb ? "Rådgiver" : "Adviser"} />
              </label>
              <label>
                {nb ? "Arbeidsgivers navn" : "Employer name"}
                <input type="text" value={drofEmployer} onChange={e => setDrofEmployer(e.target.value)} placeholder="Acme AS" />
              </label>
              <label>
                {nb ? "Planlagt oppsigelsesdato (valgfritt)" : "Planned notice date (optional)"}
                <input type="date" value={drofNoticeDate} onChange={e => setDrofNoticeDate(e.target.value)} />
              </label>
              <label className="label-full">
                {nb ? "Begrunnelse / sakens tema" : "Reason / topic"}
                <input type="text" value={drofReason} onChange={e => setDrofReason(e.target.value)} />
              </label>
            </div>
            <button className="primary" onClick={handleDroftingsmote} disabled={loading}>
              {loading ? "..." : (nb ? "Generer protokoll" : "Generate protocol")} ↗
            </button>

            {drofResult?.status === "generated" && (
              <div className="calc-result" role="status">
                <div className="result-badge info">📋 {drofResult.title}</div>
                <div className="drof-meta">
                  <span>🏢 {drofResult.employer}</span>
                  <span>📅 {nb ? "Frist for møte:" : "Meeting deadline:"} <strong>{drofResult.must_hold_before}</strong></span>
                  <code className="provision-tag">{drofResult.provision}</code>
                </div>

                <div className="legal-req-box">
                  ⚖️ <em>{drofResult.legal_requirement}</em>
                </div>

                <h4>{nb ? "Sjekkliste" : "Checklist"}</h4>
                <ul className="drof-checklist">
                  {drofResult.checklist.map((c: any, i: number) => (
                    <li key={i} className={`drof-item ${c.critical ? "critical" : "optional"}`}>
                      <span className="drof-check">{c.critical ? "🔴" : "🟡"}</span>
                      {c.item}
                      {c.critical && <span className="req-tag">{nb ? "PÅKREVD" : "REQUIRED"}</span>}
                    </li>
                  ))}
                </ul>

                <h4>{nb ? "Agendaforslag" : "Suggested agenda"}</h4>
                <ol className="drof-agenda">
                  {drofResult.agenda_template.map((line: string, i: number) => (
                    <li key={i}>{line.replace(/^\d+\.\s/, "")}</li>
                  ))}
                </ol>

                <div className="warning-banner">
                  ⚠️ {drofResult.warning}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            3. SLUTTOPPGJØR CALCULATOR
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "sluttoppgjor" && (
          <div className="calc-tool">
            <h3>{nb ? "Sluttoppgjør & lønnstrekk-sjekker (§ 14-15 / Ferieloven § 11)" : "Final Settlement & Deduction Checker (§ 14-15 / Holiday Act § 11)"}</h3>
            <p className="meta">
              {nb
                ? "Beregner alle komponenter i sluttoppgjøret ved opphør: lønn i oppsigelsesperioden, opptjente feriepenger, skyldig ferie og utlegg. Advarer om § 14-15-forbudet mot ulovlig lønnstrekk."
                : "Calculates all final settlement components on termination: notice wages, accrued holiday pay, owed vacation days and outstanding expenses. Warns about the § 14-15 salary deduction prohibition."}
            </p>
            <div className="calc-grid">
              <label>
                {nb ? "Månedlig bruttolønn (NOK)" : "Monthly gross salary (NOK)"}
                <input type="number" step="1000" value={sluttMonthlySalary} onChange={e => setSluttMonthlySalary(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Oppsigelsestid (måneder)" : "Notice period (months)"}
                <input type="number" min="0" max="12" value={sluttNoticeMonths} onChange={e => setSluttNoticeMonths(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Feriepengegrunnlag (opptjent lønn siste år)" : "Holiday pay qualifying salary"}
                <input type="number" step="10000" value={sluttHolidayBasis} onChange={e => setSluttHolidayBasis(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Alder" : "Age"}
                <input type="number" min="16" max="80" value={sluttAge} onChange={e => setSluttAge(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Skyldig ferie (virkedager, 0 = ingen)" : "Owed vacation days (0 = none)"}
                <input type="number" min="0" max="60" value={sluttVacationDays} onChange={e => setSluttVacationDays(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Ubetalte utlegg (NOK, 0 = ingen)" : "Outstanding expenses (NOK, 0 = none)"}
                <input type="number" min="0" step="100" value={sluttExpenses} onChange={e => setSluttExpenses(Number(e.target.value))} />
              </label>
            </div>
            <button className="primary" onClick={handleSluttoppgjor} disabled={loading}>
              {loading ? "..." : (nb ? "Beregn sluttoppgjør" : "Calculate settlement")} ↗
            </button>

            {sluttResult?.status === "calculated" && (
              <div className="calc-result" role="status">
                <div className="result-badge success">
                  💰 {nb ? "Totalt sluttoppgjør:" : "Total settlement:"} {sluttResult.total_nok.toLocaleString(nb ? "nb-NO" : "en-GB")} NOK
                </div>

                <table className="sluttoppgjor-table">
                  <thead>
                    <tr>
                      <th>{nb ? "Komponent" : "Component"}</th>
                      <th>{nb ? "Beløp (NOK)" : "Amount (NOK)"}</th>
                      <th>{nb ? "Hjemmel" : "Provision"}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sluttResult.components.map((c: any, i: number) => (
                      <tr key={i}>
                        <td>{c.label}</td>
                        <td className="amount-cell">{c.amount_nok.toLocaleString(nb ? "nb-NO" : "en-GB")}</td>
                        <td><code>{c.provision}</code></td>
                      </tr>
                    ))}
                    <tr className="total-row">
                      <td><strong>{nb ? "TOTALT" : "TOTAL"}</strong></td>
                      <td className="amount-cell"><strong>{sluttResult.total_nok.toLocaleString(nb ? "nb-NO" : "en-GB")}</strong></td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>

                <div className="warnings-block">
                  {sluttResult.warnings.map((w: string, i: number) => (
                    <div key={i} className="warning-item">⚠️ {w}</div>
                  ))}
                </div>
              </div>
            )}
            {sluttResult?.status === "insufficient_input" && (
              <div className="calc-result"><div className="result-badge warning">⚠ {sluttResult.reason}</div></div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            4. NOTICE PERIOD (existing)
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "notice" && (
          <div className="calc-tool">
            <h3>{nb ? "Beregning av lovbestemt oppsigelsesfrist (§ 15-3)" : "Statutory Notice Period Calculation (§ 15-3)"}</h3>
            <p className="meta">{nb ? "Tar høyde for ansiennitet, aldersintervaller (50, 55, 60 år), prøvetid og månedsskifteregelen." : "Calculates notice tenure brackets, senior age bands, probation and month-end rule."}</p>
            <div className="calc-grid">
              <label>
                {nb ? "Ansiennitet (antall år)" : "Years of service"}
                <input type="number" min="0" step="0.5" value={yearsEmployed} onChange={e => setYearsEmployed(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Arbeidstakers alder" : "Employee age"}
                <input type="number" min="16" max="80" value={age} onChange={e => setAge(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Dato for oppsigelsesvarsel" : "Notice delivery date"}
                <input type="date" value={noticeDate} onChange={e => setNoticeDate(e.target.value)} />
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={inProbation} onChange={e => setInProbation(e.target.checked)} />
                {nb ? "Ansettelsen er i avtalt prøvetid" : "Employment is in agreed probation"}
              </label>
            </div>
            <button className="primary" onClick={handleCalculateNotice} disabled={loading}>
              {loading ? "..." : (nb ? "Beregn" : "Calculate")} ↗
            </button>
            {noticeResult && (
              <div className="calc-result" role="status">
                <div className="result-badge success">✓ {noticeResult.label} ({noticeResult.provision})</div>
                <div className="result-details">
                  <p><strong>{nb ? "Oppsigelsesfrist:" : "Notice Period:"}</strong> {noticeResult.label}</p>
                  {noticeResult.notice_start && (
                    <p><strong>{nb ? "Fristen løper fra:" : "Notice period starts:"}</strong> {noticeResult.notice_start} ({nb ? "første dag i påfølgende måned" : "first of following month"})</p>
                  )}
                  {noticeResult.period_end && (
                    <p><strong>{nb ? "Siste arbeidsdag:" : "Final employment date:"}</strong> {noticeResult.period_end}</p>
                  )}
                  {noticeResult.employee_resignation_notice && (
                    <p className="meta">ℹ️ {nb ? "Ved oppsigelse fra arbeidstakers side:" : "If employee resigns:"} {noticeResult.employee_resignation_notice}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            5. CONTRACT AUDIT (existing)
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "contract" && (
          <div className="calc-tool">
            <h3>{nb ? "Obligatoriske klausuler i arbeidsavtale (§ 14-6)" : "Mandatory Employment Contract Clauses (§ 14-6)"}</h3>
            <p className="meta">{nb ? "Arbeidsmiljøloven § 14-6 krever at alle arbeidsavtaler inneholder disse lovbestemte punktene." : "Norwegian law mandates these core clauses in every employment agreement."}</p>
            <div className="checklist-grid">
              {[
                ["parties", nb ? "Partenes identitet" : "Identity of parties"],
                ["workplace", nb ? "Arbeidssted / forretningsadresse" : "Workplace / location"],
                ["role", nb ? "Stillingstittel eller beskrivelse" : "Job title / description"],
                ["start_date", nb ? "Oppstartsdato" : "Start date"],
                ["pay", nb ? "Lønn, tillegg og lønnstermin" : "Salary and components"],
                ["working_time", nb ? "Normal arbeidstid og pauser" : "Working hours and breaks"],
                ["holiday", nb ? "Ferie og feriepengerettigheter" : "Holiday and holiday pay"],
                ["notice", nb ? "Oppsigelsesfrister" : "Notice periods"],
              ].map(([key, label]) => (
                <label key={key} className="checkbox-card">
                  <input type="checkbox" checked={Boolean(contractFields[key])} onChange={e => setContractFields({ ...contractFields, [key]: e.target.checked })} />
                  <span>{label}</span>
                </label>
              ))}
            </div>
            <button className="primary" onClick={handleAuditContract} disabled={loading}>
              {loading ? "..." : (nb ? "Kontroller" : "Audit")} ↗
            </button>
            {contractResult && (
              <div className="calc-result" role="status">
                <div className={`result-badge ${contractResult.status === "ready_for_review" ? "success" : "warning"}`}>
                  {contractResult.status === "ready_for_review" ? "✓ Alle 8 obligatoriske kjerneledd er inkludert" : `! Mangler ${contractResult.missing_clauses?.length} obligatoriske klausuler`}
                </div>
                {contractResult.missing_clauses?.length > 0 && (
                  <div className="missing-box">
                    <strong>{nb ? "Mangler som må tas inn i avtalen:" : "Clauses required by § 14-6:"}</strong>
                    <ul>{contractResult.missing_clauses.map((m: string) => <li key={m}>{m}</li>)}</ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            6. HOLIDAY PAY (existing)
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "holiday" && (
          <div className="calc-tool">
            <h3>{nb ? "Beregning av ferie og feriepenger (Ferieloven)" : "Annual Leave and Holiday Pay Calculator"}</h3>
            <p className="meta">{nb ? "Lovfestet feriefritid er 25 virkedager (4 uker + 1 dag). Arbeidstakere fra 60 år har rett på en ekstra ferieuke og forhøyet sats." : "Statutory vacation is 25 weekdays. Employees aged 60+ receive 1 extra week and higher percentage."}</p>
            <div className="calc-grid">
              <label>
                {nb ? "Feriepengegrunnlag (opptjent lønn i fjor)" : "Gross salary in qualifying year"}
                <input type="number" step="10000" value={salaryBasis} onChange={e => setSalaryBasis(Number(e.target.value))} />
              </label>
              <label>
                {nb ? "Alder ved ferieårets start" : "Employee age"}
                <input type="number" value={holidayAge} onChange={e => setHolidayAge(Number(e.target.value))} />
              </label>
            </div>
            <button className="primary" onClick={handleCalculateHoliday} disabled={loading}>
              {loading ? "..." : (nb ? "Beregn" : "Calculate")} ↗
            </button>
            {holidayResult && (
              <div className="calc-result" role="status">
                <div className="result-badge success">✓ {holidayResult.holiday_pay_rate_pct}% feriepenger ({holidayResult.vacation_weeks_statutory})</div>
                <div className="result-details">
                  <p><strong>{nb ? "Lovfestet feriefritid:" : "Statutory holiday days:"}</strong> {holidayResult.vacation_days_statutory} virkedager ({holidayResult.vacation_weeks_statutory})</p>
                  <p><strong>{nb ? "Lovbestemt feriepengesats:" : "Statutory percentage:"}</strong> {holidayResult.holiday_pay_rate_pct}% {holidayAge >= 60 ? "(inkl. 2,3% senior-tillegg)" : ""}</p>
                  {holidayResult.estimated_holiday_pay_nok && (
                    <p><strong>{nb ? "Beregnet feriepengebeløp:" : "Estimated holiday pay:"}</strong> {holidayResult.estimated_holiday_pay_nok.toLocaleString()} NOK</p>
                  )}
                  <p className="meta">Kilde: {holidayResult.provision}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════════
            7. NOTICE FORM CHECK (existing)
        ════════════════════════════════════════════════════════════════════ */}
        {activeTool === "form" && (
          <div className="calc-tool">
            <h3>{nb ? "Kontroll av formfeil ved oppsigelse (§ 15-4 & § 15-5)" : "Termination Notice Form Audit (§ 15-4 & § 15-5)"}</h3>
            <p className="meta">{nb ? "Dersom en oppsigelse mangler lovpålagte opplysninger, kan den kjennes ugyldig og utløse erstatningsansvar etter § 15-5." : "Defective notices without statutory lawsuit/negotiation information can trigger court invalidation."}</p>
            <div className="checklist-grid">
              {[
                ["written", nb ? "Gitt skriftlig" : "In writing"],
                ["personal_or_registered", nb ? "Levert personlig eller sendt rekommandert" : "Hand-delivered or registered mail"],
                ["negotiation_rights", nb ? "Opplyser om rett til forhandling (2 uker frist)" : "Informs of right to demand negotiation (2 weeks)"],
                ["lawsuit_rights", nb ? "Opplyser om rett til søksmål (8 uker frist)" : "Informs of right to file lawsuit (8 weeks)"],
                ["stay_in_post_rights", nb ? "Opplyser om retten til å fortsette i stillingen" : "Informs of right to remain in post"],
                ["correct_defendant", nb ? "Opplyser om hvem som er rett arbeidsgiver/saksøkt" : "Identifies correct employer legal entity"],
              ].map(([key, label]) => (
                <label key={key} className="checkbox-card">
                  <input type="checkbox" checked={Boolean(formChecks[key])} onChange={e => setFormChecks({ ...formChecks, [key]: e.target.checked })} />
                  <span>{label}</span>
                </label>
              ))}
            </div>
            <button className="primary" onClick={handleCheckForm} disabled={loading}>
              {loading ? "..." : (nb ? "Kontroller" : "Audit")} ↗
            </button>
            {formResult && (
              <div className="calc-result" role="status">
                <div className={`result-badge ${formResult.is_formally_valid ? "success" : "danger"}`}>
                  {formResult.is_formally_valid
                    ? (nb ? "✓ Oppsigelsen oppfyller alle lovpålagte formkrav (§ 15-4)" : "✓ The termination notice meets all statutory formal requirements (section 15-4)")
                    : (nb ? "! Formfeil oppdaget i oppsigelsesbrevet" : "! Formal defects found in the termination notice")}
                </div>
                {!formResult.is_formally_valid && (
                  <div className="missing-box danger">
                    <strong>{nb ? "Følgende obligatoriske opplysninger mangler:" : "Missing mandatory information:"}</strong>
                    <ul>{formResult.missing_mandatory_elements.map((m: string) => <li key={m}>{m}</li>)}</ul>
                    <p className="warning-text">{formResult.consequence_of_defect}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
