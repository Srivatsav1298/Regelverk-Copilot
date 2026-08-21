import type { Answer, Assessment, CaseInput, Language, Audience } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const ask = (question: string, language: Language, audience: Audience) =>
  request<Answer>("/api/v1/ask", { method: "POST", body: JSON.stringify({ question, language, audience }) });

export const assess = (input: CaseInput) =>
  request<Assessment>("/api/v1/assess", { method: "POST", body: JSON.stringify(input) });

export async function brief(input: CaseInput, assessment: Assessment) {
  const response = await fetch(`${API_BASE}/api/v1/brief`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ case: input, assessment }) });
  if (!response.ok) throw new Error(`Brief failed (${response.status})`);
  return response.text();
}
