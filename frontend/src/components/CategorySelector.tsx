import type { Topic, Language } from "../types";

interface CategorySelectorProps {
  topics: Topic[];
  selectedDomain: string;
  onSelectCategory: (domain: string, samplePrompt?: string) => void;
  language: Language;
}

const CATEGORY_ICONS: Record<string, string> = {
  termination: "🛡️",
  contracts: "📄",
  working_time: "⏱️",
  holidays: "🏖️",
  leave: "👶",
  sickness: "🩺",
  workplace_rights: "📢",
  disputes: "⚖️",
  temporary_work: "⏳",
  pay: "💰",
  equality: "🤝",
  reporting: "📊",
};

const ENGLISH_CATEGORIES: Record<string, { label: string; description: string }> = {
  termination: { label: "Termination and dismissal", description: "Discussion meetings, grounds, protections, formal requirements, notice periods, suspension and dismissal." },
  contracts: { label: "Employment contracts and hiring", description: "Legal requirements for contracts, probation, employee versus contractor status and changes." },
  working_time: { label: "Working hours and overtime", description: "Ordinary hours, overtime limits, the 40% overtime supplement, breaks and rest." },
  holidays: { label: "Holiday and holiday pay", description: "Statutory holiday, holiday planning, holiday-pay basis and final settlements." },
  leave: { label: "Leave and parental rights", description: "Pregnancy, birth, adoption and special dismissal protection during leave." },
  sickness: { label: "Sick leave and protection", description: "Sick leave, 12-month dismissal protection and documentation requirements." },
  workplace_rights: { label: "Whistleblowing and workplace", description: "The right to report concerns, protection against retaliation and harassment safeguards." },
  disputes: { label: "Disputes and court deadlines", description: "Negotiation requirements, court deadlines and the right to remain in post." },
  temporary_work: { label: "Temporary employment", description: "Requirements for temporary roles, replacements and conversion to permanent employment." },
  pay: { label: "Pay and wage deductions", description: "Minimum pay, wage deductions and final settlements." },
  equality: { label: "Equality and discrimination", description: "Equality and anti-discrimination rules and protection from unequal treatment." },
  reporting: { label: "Public reporting", description: "Collective redundancy notices, payroll reporting and public obligations." },
};

export function CategorySelector({
  topics,
  selectedDomain,
  onSelectCategory,
  language,
}: CategorySelectorProps) {
  const t = language === "nb" ? {
    title: "Utforsk rettsområder",
    all: "Alle temaer",
    supported: "Støttet",
    planned: "Kommer",
  } : {
    title: "Explore Legal Categories",
    all: "All categories",
    supported: "Supported",
    planned: "Planned",
  };

  return (
    <section className="categories-section" aria-label={t.title}>
      <div className="section-title-row">
        <h3>{t.title}</h3>
      </div>
      <div className="category-chips">
        <button
          className={`chip ${selectedDomain === "all" ? "active" : ""}`}
          onClick={() => onSelectCategory("all")}
        >
          {t.all}
        </button>
        {topics.map((topic) => {
          // The API catalogue mirrors the Norwegian source registry; the
          // presentation layer localises it for English users.
          const copy = language === "en" ? ENGLISH_CATEGORIES[topic.domain] : undefined;
          const label = copy?.label ?? topic.label;
          const description = copy?.description ?? topic.description;
          return (
            <button
              key={topic.domain}
              className={`chip ${selectedDomain === topic.domain ? "active" : ""} ${topic.status}`}
              onClick={() => onSelectCategory(topic.domain, description)}
            >
              <span>{CATEGORY_ICONS[topic.domain] || "📌"}</span>
              <span>{label}</span>
              {topic.status === "planned" && <span className="chip-badge">{t.planned}</span>}
            </button>
          );
        })}
      </div>
    </section>
  );
}
