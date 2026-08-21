export type Language = "nb" | "en";
export type Audience = "employer" | "employee";

export interface Citation { source_name: string; excerpt: string }
export interface Corpus { corpus_version: string; freshness_warning: boolean; publication_or_update_date: string; source_url: string }
export interface Answer {
  answer: string; citations: Citation[]; confidence: "high" | "low"; disclaimer: string;
  corpus?: Corpus; escalation_level?: "none" | "review" | "urgent"; trace?: Record<string, unknown>;
}
export interface CaseInput {
  situation: string; domain: string; audience: Audience; termination_reason: string;
  employee_age: number | null; years_employed: number | null; on_sick_leave: boolean;
  pregnant_or_parental_leave: boolean; in_probation: boolean; immediate_dismissal: boolean;
  notice_date: string | null; language: Language;
}
export interface Assessment {
  summary: string; risk_level: "low" | "medium" | "high" | "unknown"; next_steps: string[];
  questions_to_confirm: string[]; citations: Citation[]; confidence: "high" | "low";
  disclaimer: string; corpus?: Corpus; escalation_level?: "none" | "review" | "urgent";
}
