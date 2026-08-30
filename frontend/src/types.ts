export type Language = "nb" | "en";
export type Audience = "employer" | "employee";

export interface Citation { source_name: string; excerpt: string; url?: string; verified?: boolean; source_status?: string }
export interface Corpus { corpus_version: string; freshness_warning: boolean; publication_or_update_date: string; source_url: string; sources?: Array<Record<string, string>> }
export interface Topic { domain: string; label: string; status: "supported" | "planned" | "under_review"; depth?: string; description: string }
export interface Workflow { id: string; domain: string; label: string; description: string }
export interface Answer {
  answer: string; citations: Citation[]; confidence: "high" | "low"; disclaimer: string;
  corpus?: Corpus; escalation_level?: "none" | "review" | "urgent"; trace?: Record<string, unknown>;
  domain?: string; subtopic?: string; applicability?: string[]; clarifying_questions?: string[]; related_topics?: string[]; calculation_results?: Record<string, unknown>; escalation_reasons?: string[];
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
  domain?: string; subtopic?: string; applicability?: string[]; clarifying_questions?: string[]; related_topics?: string[]; calculation_results?: Record<string, unknown>; escalation_reasons?: string[];
}
