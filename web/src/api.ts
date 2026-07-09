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
  concepts?: string[];
  objective?: string | null;
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

export interface ActivityPoint {
  date: string;
  reviews: number;
  good: number;
  again: number;
}

export interface RetentionTrendPoint {
  period: string;
  reviews: number;
  retention_pct: number;
}

export interface RatingBucket {
  rating: number;
  label: string;
  count: number;
}

export interface DeckWorkload {
  label: string;
  due: number;
  total: number;
}

export interface RetrievabilityPoint {
  date: string;
  avg_retrievability: number;
}

export interface AnalyticsDashboard {
  overview: AnalyticsOverview;
  activity: ActivityPoint[];
  retention_trend: RetentionTrendPoint[];
  ratings: RatingBucket[];
  deck_workload: DeckWorkload[];
  mastery_top: ConceptMastery[];
  mastery_bottom: ConceptMastery[];
  retrievability_trend: RetrievabilityPoint[];
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

export interface LibraryNode {
  id: string;
  label: string;
  kind: string;
  path?: string | null;
  slug?: string | null;
  due_count: number;
  card_count: number;
  mastery_score?: number | null;
  children: LibraryNode[];
}

export interface CollectionSummary {
  id: number;
  slug: string;
  title: string;
  description?: string | null;
  due_count: number;
  card_count: number;
}

export interface TrackStepSummary {
  step_index: number;
  step_type: string;
  match: string;
  due_count: number;
  card_count: number;
  completed: boolean;
}

export interface TrackSummary {
  id: string;
  title: string;
  description?: string | null;
  current_step: number;
  total_steps: number;
  steps: TrackStepSummary[];
  focus_deck_prefix?: string | null;
  focus_concept_slug?: string | null;
}

export interface LearningLibrary {
  collection: CollectionSummary | null;
  collections: CollectionSummary[];
  modules: LibraryNode[];
  topics: LibraryNode[];
  tracks: TrackSummary[];
}

export interface ReviewFocusParams {
  deck?: string;
  concept?: string;
  track?: string;
}

function focusQuery(params?: ReviewFocusParams): string {
  if (!params) return "";
  const search = new URLSearchParams();
  if (params.deck) search.set("deck_prefix", params.deck);
  if (params.concept) search.set("concept_slug", params.concept);
  if (params.track) search.set("track_id", params.track);
  const query = search.toString();
  return query ? `?${query}` : "";
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
    let detail = `Request failed (${response.status})`;
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      if (parsed.detail) {
        detail =
          response.status === 404
            ? "Endpoint not found — restart `deckflow serve` and use http://localhost:5173"
            : parsed.detail;
      }
    } catch {
      if (body) detail = body;
    }
    throw new Error(detail);
  }

  if (response.status === 204 || !body) {
    return undefined as T;
  }

  return JSON.parse(body) as T;
}

export function fetchStats(): Promise<Stats> {
  return request<Stats>("/stats");
}

export function fetchNextCard(focus?: ReviewFocusParams): Promise<Card | null> {
  return request<Card | null>(`/review/next${focusQuery(focus)}`);
}

export function submitReview(
  cardId: number,
  rating: number,
  telemetry?: {
    reveal_ms?: number;
    rating_ms?: number;
    session_id?: number;
  },
): Promise<{ card_id: number; due: string; reps: number; session_id: number }> {
  return request(`/review/${cardId}`, {
    method: "POST",
    body: JSON.stringify({ rating, ...telemetry }),
  });
}

export function resetReviewSession(): Promise<void> {
  return request<void>("/review/session/reset", { method: "POST" });
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

export function fetchAnalyticsDashboard(): Promise<AnalyticsDashboard> {
  return request<AnalyticsDashboard>("/analytics/dashboard");
}

export function fetchConceptMastery(): Promise<ConceptMastery[]> {
  return request<ConceptMastery[]>("/analytics/concepts");
}

export function fetchWeakSpots(): Promise<WeakSpot[]> {
  return request<WeakSpot[]>("/analytics/weak-spots");
}

export function fetchStudyPlan(focus?: ReviewFocusParams): Promise<StudyPlanItem[]> {
  return request<StudyPlanItem[]>(`/study-plan/today${focusQuery(focus)}`);
}

export function fetchLibrary(): Promise<LearningLibrary> {
  return request<LearningLibrary>("/library");
}
