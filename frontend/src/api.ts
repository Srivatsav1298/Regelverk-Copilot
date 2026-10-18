import type { Answer, Assessment, CaseInput, Language, Audience, Topic, Workflow, CalculationResult, Corpus } from "./types";

// Local builds may be served from Vite, port 3000, or a static preview server.
// Always target the local API on localhost; deployed domains remain same-origin.
const isLocalHost = typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_BASE = import.meta.env.VITE_API_BASE ?? (isLocalHost ? "http://127.0.0.1:8000" : "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const ask = (question: string, language: Language, audience: Audience) =>
  request<Answer>("/api/v1/ask", {
    method: "POST",
    body: JSON.stringify({ question, language, audience }),
  });

export const assess = (input: CaseInput) =>
  request<Assessment>("/api/v1/assess", {
    method: "POST",
    body: JSON.stringify(input),
  });

export async function brief(input: CaseInput, assessment: Assessment): Promise<string> {
  const response = await fetch(`${API_BASE}/api/v1/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case: input, assessment }),
  });
  if (!response.ok) throw new Error(`Brief failed (${response.status})`);
  return response.text();
}

export const getTopics = () =>
  request<{ topics: Topic[]; workflows: Workflow[] }>("/api/v1/topics");

export const getSources = () =>
  request<Corpus>("/api/v1/sources");

export const calculateRule = (rule: string, inputs: Record<string, any>, language: Language = "nb") =>
  request<CalculationResult>("/api/v1/calculate", {
    method: "POST",
    body: JSON.stringify({ rule, inputs, language }),
  });

export const sendCorrection = (payload: { helpful?: boolean; category?: string; message?: string }) =>
  request("/api/v1/corrections", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const recordVisit = (visitorId: string) =>
  request<{ daily_visitors: number }>("/api/v1/visits", {
    method: "POST",
    body: JSON.stringify({ visitor_id: visitorId }),
  });

export const getFreshness = () =>
  request<{ source_monitor?: { status: "current" | "changed" | "unavailable" | string } }>("/api/v1/freshness");
