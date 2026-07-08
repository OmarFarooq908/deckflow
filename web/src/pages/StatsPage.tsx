import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AnalyticsOverview,
  ConceptMastery,
  Deck,
  Stats,
  StudyPlanItem,
  WeakSpot,
  fetchAnalyticsOverview,
  fetchConceptMastery,
  fetchDecks,
  fetchStats,
  fetchStudyPlan,
  fetchWeakSpots,
} from "../api";

export function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [concepts, setConcepts] = useState<ConceptMastery[]>([]);
  const [weakSpots, setWeakSpots] = useState<WeakSpot[]>([]);
  const [plan, setPlan] = useState<StudyPlanItem[]>([]);
  const [decks, setDecks] = useState<Deck[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchStats(),
      fetchAnalyticsOverview(),
      fetchConceptMastery(),
      fetchWeakSpots(),
      fetchStudyPlan(),
      fetchDecks(),
    ])
      .then(([statsData, overviewData, conceptsData, spotsData, planData, deckData]) => {
        setStats(statsData);
        setOverview(overviewData);
        setConcepts(conceptsData);
        setWeakSpots(spotsData);
        setPlan(planData);
        setDecks(deckData);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) {
    return <div className="panel error">{error}</div>;
  }

  if (!stats || !overview) {
    return <div className="panel">Loading analytics...</div>;
  }

  return (
    <div className="panel">
      <h1>Learning Analytics</h1>

      <h2>Overview</h2>
      <div className="stat-grid">
        <div className="stat-card">
          <span className="muted">Retention (7d)</span>
          <strong>{overview.retention_7d}%</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Retention (30d)</span>
          <strong>{overview.retention_30d}%</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Cards/day (7d)</span>
          <strong>{overview.cards_per_day_7d}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Avg mastery</span>
          <strong>{overview.avg_mastery}%</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Due today</span>
          <strong>{stats.due_today}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Streak</span>
          <strong>{overview.streak_days} days</strong>
        </div>
      </div>

      <h2>Today's plan</h2>
      {plan.length === 0 ? (
        <p className="muted">No cards queued for today.</p>
      ) : (
        <ul className="plan-list">
          {plan.slice(0, 8).map((item) => (
            <li key={item.card_id}>
              <strong>{item.front_preview}</strong>
              <span className="muted"> — {item.reason}</span>
            </li>
          ))}
        </ul>
      )}

      <h2>Weak spots</h2>
      {weakSpots.length === 0 ? (
        <p className="muted">No weak spots detected yet. Keep reviewing.</p>
      ) : (
        <ul className="weak-list">
          {weakSpots.map((spot) => (
            <li key={spot.concept_slug}>{spot.message}</li>
          ))}
        </ul>
      )}

      <h2>Domain mastery</h2>
      {concepts.length === 0 ? (
        <p className="muted">Import a deck and review cards to build mastery data.</p>
      ) : (
        <div className="mastery-list">
          {concepts.slice(0, 12).map((concept) => (
            <div key={concept.concept_id} className="mastery-row">
              <div className="mastery-label">
                <span>{concept.slug}</span>
                <span className="muted">{concept.mastery_score.toFixed(0)}%</span>
              </div>
              <div className="mastery-bar">
                <div
                  className="mastery-fill"
                  style={{ width: `${concept.mastery_score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <h2>Decks</h2>
      {decks.length === 0 ? (
        <p className="muted">No decks imported yet.</p>
      ) : (
        <ul>
          {decks.map((deck) => (
            <li key={deck.id}>
              {deck.path} — {deck.due_count} due / {deck.card_count} total
            </li>
          ))}
        </ul>
      )}

      <div className="actions">
        <Link className="btn" to="/review">
          Start review
        </Link>
        <Link className="btn secondary" to="/">
          Back home
        </Link>
      </div>
    </div>
  );
}
