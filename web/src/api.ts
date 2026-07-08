const API_BASE = "/api";

export interface Stats {
  due_today: number;
  new_cards: number;
  reviewed_today: number;
  total_cards: number;
  retention_pct: number;
  streak_days: number;
  last_import_path: string | null;
}

export interface Card {
  id: number;
  deck_path: string;
  front_md: string;
  back_md: string;
  card_type: string | null;
  tags: string[];
  hint?: string | null;
  links?: string[];
  queue_reason?: string | null;
}

export interface Deck {
  id: number;
  path: string;
  card_count: number;
  due_count: number;
}

export interface AnalyticsOverview {
  retention_7d: number;
  retention_30d: number;
  cards_per_day_7d: number;
  avg_mastery: number;
  streak_days: number;
  due_today: number;
  reviewed_today: number;
  total_cards: number;
}

export interface ConceptMastery {
  concept_id: number;
  slug: string;
  label: string;
  card_count: number;
  reviews_count: number;
  retention_7d: number;
  retention_30d: number;
  mastery_score: number;
  weakness_score: number;
}

export interface WeakSpot {
  concept_slug: string;
  concept_label: string;
  mastery_score: number;
  retention_7d: number;
  lapse_count: number;
  message: string;
}

export interface StudyPlanItem {
  card_id: number;
  card_uid: string | null;
  deck_path: string;
  front_preview: string;
  reason: string;
  score: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  const contentType = response.headers.get("content-type") ?? "";
  const body = await response.text();

  if (!contentType.includes("application/json")) {
    throw new Error(
      "API unreachable — start the backend with `deckflow serve` and open the UI at http://localhost:5173 (not 5174).",
    );
  }

  if (!response.ok) {
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      throw new Error(parsed.detail || `Request failed: ${response.status}`);
    } catch {
      throw new Error(body || `Request failed: ${response.status}`);
    }
  }

  if (response.status === 204 || !body) {
    return undefined as T;
  }

  return JSON.parse(body) as T;
}

export function fetchStats(): Promise<Stats> {
  return request<Stats>("/stats");
}

export function fetchNextCard(): Promise<Card | null> {
  return request<Card | null>("/review/next");
}

export function submitReview(
  cardId: number,
  rating: number,
  telemetry?: { reveal_ms?: number; rating_ms?: number },
): Promise<{ card_id: number; due: string; reps: number }> {
  return request(`/review/${cardId}`, {
    method: "POST",
    body: JSON.stringify({ rating, ...telemetry }),
  });
}

export function importDeck(
  path: string,
): Promise<{ imported: number; decks: number; path: string }> {
  return request("/import", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
}

export function fetchDecks(): Promise<Deck[]> {
  return request<Deck[]>("/decks");
}

export function fetchAnalyticsOverview(): Promise<AnalyticsOverview> {
  return request<AnalyticsOverview>("/analytics/overview");
}

export function fetchConceptMastery(): Promise<ConceptMastery[]> {
  return request<ConceptMastery[]>("/analytics/concepts");
}

export function fetchWeakSpots(): Promise<WeakSpot[]> {
  return request<WeakSpot[]>("/analytics/weak-spots");
}

export function fetchStudyPlan(): Promise<StudyPlanItem[]> {
  return request<StudyPlanItem[]>("/study-plan/today");
}
