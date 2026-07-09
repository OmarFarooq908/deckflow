import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, HelpCircle } from "lucide-react";
import {
  Card as ApiCard,
  ReviewFocusParams,
  fetchNextCard,
  resetReviewSession,
  submitReview,
} from "@/api";
import { CardAnalyticsPanel } from "@/components/CardAnalyticsPanel";
import { DeckBreadcrumb } from "@/components/DeckBreadcrumb";
import { EmptyState } from "@/components/EmptyState";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingState } from "@/components/LoadingState";
import { MarkdownCard } from "@/components/MarkdownCard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useStatsContext } from "@/hooks/useStatsContext";
import { cn } from "@/lib/utils";

const RATINGS = [
  { value: 1, label: "Again", className: "bg-red-500 hover:bg-red-600" },
  { value: 2, label: "Hard", className: "bg-amber-500 hover:bg-amber-600" },
  { value: 3, label: "Good", className: "bg-green-500 hover:bg-green-600" },
  { value: 4, label: "Easy", className: "bg-cyan-500 hover:bg-cyan-600" },
] as const;

function focusLabel(focus: ReviewFocusParams): string | null {
  if (focus.deck) {
    const parts = focus.deck.split("::");
    return parts[parts.length - 1] ?? focus.deck;
  }
  if (focus.concept) {
    const parts = focus.concept.split("::");
    return parts[parts.length - 1] ?? focus.concept;
  }
  if (focus.track) return `track: ${focus.track}`;
  return null;
}

export function ReviewPage() {
  const [searchParams] = useSearchParams();
  const deck = searchParams.get("deck") ?? undefined;
  const concept = searchParams.get("concept") ?? undefined;
  const track = searchParams.get("track") ?? undefined;
  const focus: ReviewFocusParams = { deck, concept, track };
  const studying = focusLabel(focus);
  const { refresh: refreshStats } = useStatsContext();

  const [card, setCard] = useState<ApiCard | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [done, setDone] = useState(false);
  const [skippedAll, setSkippedAll] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const shownAt = useRef<number>(Date.now());
  const revealedAt = useRef<number | null>(null);
  const sessionId = useRef<number | undefined>(undefined);
  const submittingRef = useRef(false);
  const skippedCardIds = useRef<Set<number>>(new Set());

  useEffect(() => {
    sessionId.current = undefined;
    skippedCardIds.current = new Set();
    void resetReviewSession().catch(() => undefined);
  }, [deck, concept, track]);

  const loadNext = useCallback(async () => {
    setLoading(true);
    setError(null);
    setRevealed(false);
    revealedAt.current = null;
    const focusParams: ReviewFocusParams = { deck, concept, track };
    const excludeCardIds = [...skippedCardIds.current];
    try {
      const next = await fetchNextCard(focusParams, excludeCardIds);
      const skippedCount = skippedCardIds.current.size;
      setCard(next);
      setSkippedAll(next === null && skippedCount > 0);
      setDone(next === null);
      shownAt.current = Date.now();
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [deck, concept, track]);

  async function handleSkip() {
    if (!card || submittingRef.current) return;
    skippedCardIds.current.add(card.id);
    await loadNext();
  }

  useEffect(() => {
    void loadNext();
  }, [loadNext]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!revealed || !card || submittingRef.current) return;
      const rating = Number(event.key);
      if (rating >= 1 && rating <= 4) {
        void handleRate(rating);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revealed, card, submitting]);

  async function handleRate(rating: number) {
    if (!card || submittingRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);
    setError(null);
    const cardId = card.id;
    const now = Date.now();
    const reveal_ms = revealedAt.current
      ? revealedAt.current - shownAt.current
      : undefined;
    const rating_ms = revealedAt.current
      ? now - revealedAt.current
      : undefined;
    try {
      const result = await submitReview(cardId, rating, {
        reveal_ms,
        rating_ms,
        session_id: sessionId.current,
      });
      sessionId.current = result.session_id;
      await refreshStats();
      await loadNext();
    } catch (err) {
      setError(err);
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  if (loading) {
    return <LoadingState variant="review" />;
  }

  if (error && !card) {
    return <ErrorAlert error={error} onRetry={() => void loadNext()} />;
  }

  if (done) {
    return (
      <EmptyState
        icon={<CheckCircle2 className="h-10 w-10" />}
        title="All caught up"
        description={
          skippedAll
            ? studying
              ? `No cards left in "${studying}" (remaining due cards were skipped).`
              : "No cards left to review (due cards were skipped)."
            : studying
              ? `No cards due in "${studying}" right now.`
              : "No cards are due for review right now."
        }
        actionLabel="Browse library"
        actionTo="/library"
      />
    );
  }

  if (!card) {
    return (
      <EmptyState
        title="No card available"
        description="Import a deck or check back later."
        actionLabel="Go to Today"
        actionTo="/"
      />
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
      {studying && (
        <Alert>
          <AlertTitle className="flex items-center justify-between gap-2">
            <span>
              Studying: <strong>{studying}</strong>
            </span>
            <Button asChild variant="ghost" size="sm">
              <Link to="/review">Clear focus</Link>
            </Button>
          </AlertTitle>
        </Alert>
      )}

      <DeckBreadcrumb deckPath={card.deck_path} />

      <div className="flex flex-wrap items-center gap-2">
        {card.concepts?.map((slug) => (
          <Link
            key={slug}
            to={`/review?concept=${encodeURIComponent(slug)}`}
            className="inline-flex"
          >
            <Badge variant="secondary">
              {slug.split("::").pop() ?? slug}
            </Badge>
          </Link>
        ))}
        {card.queue_reason && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs">
                <HelpCircle className="h-3.5 w-3.5" />
                Why this card?
              </Button>
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              {card.queue_reason}
            </TooltipContent>
          </Tooltip>
        )}
        <CardAnalyticsPanel cardId={card.id} />
      </div>

      {card.objective && (
        <Alert className="border-green-500/30 bg-green-500/10">
          <AlertDescription>
            <strong>Objective:</strong> {card.objective}
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader className="pb-2">
          <p className="text-sm font-medium text-muted-foreground">
            {revealed ? "Answer" : "Question"}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <MarkdownCard content={revealed ? card.back_md : card.front_md} />

          {card.hint && !revealed && (
            <Alert>
              <AlertDescription>
                <strong>Hint:</strong> {card.hint}
              </AlertDescription>
            </Alert>
          )}

          {!revealed ? (
            <div className="space-y-2">
              <Button className="w-full" size="lg" onClick={() => {
                revealedAt.current = Date.now();
                setRevealed(true);
              }}>
                Reveal answer
              </Button>
              <Button
                className="w-full"
                variant="outline"
                size="sm"
                disabled={submitting}
                onClick={() => void handleSkip()}
              >
                Skip for now
              </Button>
            </div>
          ) : (
            <>
              {card.links && card.links.length > 0 && (
                <div className="text-sm text-muted-foreground">
                  <strong className="text-foreground">Links:</strong>
                  <ul className="mt-1 list-disc pl-5">
                    {card.links.map((link) => (
                      <li key={link}>
                        <code>{link}</code>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {RATINGS.map((rating) => (
                  <Tooltip key={rating.value}>
                    <TooltipTrigger asChild>
                      <Button
                        className={cn("w-full text-white", rating.className)}
                        disabled={submitting}
                        onClick={() => void handleRate(rating.value)}
                      >
                        {rating.label}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Press {rating.value}</TooltipContent>
                  </Tooltip>
                ))}
              </div>
              <p className="text-center text-xs text-muted-foreground">
                Keyboard: press 1–4 to rate
              </p>
              <Button
                className="w-full"
                variant="ghost"
                size="sm"
                disabled={submitting}
                onClick={() => void handleSkip()}
              >
                Skip for now
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {error ? <ErrorAlert error={error} /> : null}
    </div>
  );
}
