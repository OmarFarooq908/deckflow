import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Card, fetchNextCard, submitReview } from "../api";
import { MarkdownCard } from "../components/MarkdownCard";

const RATINGS = [
  { value: 1, label: "Again", className: "rating-again" },
  { value: 2, label: "Hard", className: "rating-hard" },
  { value: 3, label: "Good", className: "rating-good" },
  { value: 4, label: "Easy", className: "rating-easy" },
] as const;

export function ReviewPage() {
  const [card, setCard] = useState<Card | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const shownAt = useRef<number>(Date.now());
  const revealedAt = useRef<number | null>(null);

  async function loadNext() {
    setLoading(true);
    setError(null);
    setRevealed(false);
    revealedAt.current = null;
    try {
      const next = await fetchNextCard();
      setCard(next);
      setDone(next === null);
      shownAt.current = Date.now();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load card");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNext();
  }, []);

  function handleReveal() {
    revealedAt.current = Date.now();
    setRevealed(true);
  }

  async function handleRate(rating: number) {
    if (!card) return;
    setError(null);
    const now = Date.now();
    const reveal_ms = revealedAt.current
      ? revealedAt.current - shownAt.current
      : undefined;
    const rating_ms = revealedAt.current
      ? now - revealedAt.current
      : undefined;
    try {
      await submitReview(card.id, rating, { reveal_ms, rating_ms });
      await loadNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save review");
    }
  }

  if (loading) {
    return <div className="panel">Loading next card...</div>;
  }

  if (done) {
    return (
      <div className="panel">
        <h1>All caught up</h1>
        <p className="muted">No cards are due for review right now.</p>
        <div className="actions">
          <Link className="btn" to="/">
            Back home
          </Link>
        </div>
      </div>
    );
  }

  if (!card) {
    return <div className="panel">No card available.</div>;
  }

  return (
    <div className="panel">
      <p className="muted">{card.deck_path}</p>
      {card.queue_reason && (
        <p className="queue-reason">Queue: {card.queue_reason}</p>
      )}
      {card.tags.length > 0 && (
        <p className="muted">Tags: {card.tags.join(", ")}</p>
      )}
      {card.hint && !revealed && (
        <p className="hint-box">
          <strong>Hint:</strong> {card.hint}
        </p>
      )}

      <h2>Front</h2>
      <MarkdownCard content={card.front_md} />

      {!revealed ? (
        <div className="actions">
          <button className="btn" onClick={handleReveal}>
            Reveal answer
          </button>
        </div>
      ) : (
        <>
          <h2>Back</h2>
          <MarkdownCard content={card.back_md} />
          {card.links && card.links.length > 0 && (
            <div className="links-box">
              <strong>Links:</strong>
              <ul>
                {card.links.map((link) => (
                  <li key={link}>
                    <code>{link}</code>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="actions">
            {RATINGS.map((rating) => (
              <button
                key={rating.value}
                className={`btn ${rating.className}`}
                onClick={() => void handleRate(rating.value)}
              >
                {rating.label}
              </button>
            ))}
          </div>
        </>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
