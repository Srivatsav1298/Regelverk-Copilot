import type { Audience, ActiveTab, Language } from "../types";

interface QuickStartProps {
  audience: Audience;
  language: Language;
  onStart: (action: { tab: ActiveTab; prompt?: string }) => void;
}

type QuickAction = {
  icon: string;
  title: string;
  description: string;
  tab: ActiveTab;
  prompt?: string;
};

export function QuickStart({ audience, language, onStart }: QuickStartProps) {
  const nb = language === "nb";
  const actions: QuickAction[] = audience === "employer"
    ? (nb ? [
        { icon: "🩺", title: "Sykefravær og frister", description: "Få oversikt over 4-, 7-, 26- og 52-ukers frister.", tab: "tools" },
        { icon: "🧭", title: "Vurder en personalsak", description: "Sjekk vern, risiko og riktige prosess-steg.", tab: "assess" },
        { icon: "📄", title: "Kontroller arbeidsavtale", description: "Finn manglende lovpålagte klausuler på sekunder.", tab: "doc" },
      ] : [
        { icon: "🩺", title: "Sick leave deadlines", description: "See the 4-, 7-, 26- and 52-week milestones.", tab: "tools" },
        { icon: "🧭", title: "Assess an employment case", description: "Check protections, risk and the correct process.", tab: "assess" },
        { icon: "📄", title: "Audit an employment contract", description: "Find missing statutory clauses in seconds.", tab: "doc" },
      ])
    : (nb ? [
        { icon: "🩺", title: "Mine sykefraværsfrister", description: "Se hva som skjer ved 4, 7, 26 og 52 uker.", tab: "tools" },
        { icon: "⚖️", title: "Forstå oppsigelsen", description: "Få oversikt over formkrav, frister og vern.", tab: "doc" },
        { icon: "⏱️", title: "Finn oppsigelsesfristen", description: "Beregn fristen ut fra alder og ansiennitet.", tab: "tools" },
      ] : [
        { icon: "🩺", title: "My sick leave deadlines", description: "See what happens at weeks 4, 7, 26 and 52.", tab: "tools" },
        { icon: "⚖️", title: "Understand my termination", description: "Review formal requirements, deadlines and protections.", tab: "doc" },
        { icon: "⏱️", title: "Find my notice period", description: "Calculate it from age and years of service.", tab: "tools" },
      ]);

  return (
    <section className="quick-start" aria-labelledby="quick-start-title">
      <div className="quick-start-heading">
        <div>
          <p className="quick-start-kicker">{nb ? "START HER" : "START HERE"}</p>
          <h2 id="quick-start-title">{nb ? "Hva vil du løse i dag?" : "What do you need to solve today?"}</h2>
        </div>
        <span className="quick-start-context">{audience === "employer" ? (nb ? "For arbeidsgivere" : "For employers") : (nb ? "For arbeidstakere" : "For employees")}</span>
      </div>
      <div className="quick-start-grid">
        {actions.map((action) => (
          <button key={action.title} className="quick-action" onClick={() => onStart({ tab: action.tab, prompt: action.prompt })}>
            <span className="quick-action-icon" aria-hidden="true">{action.icon}</span>
            <span className="quick-action-copy"><strong>{action.title}</strong><span>{action.description}</span></span>
            <span className="quick-action-arrow" aria-hidden="true">↗</span>
          </button>
        ))}
      </div>
    </section>
  );
}
