import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { CardAnalytics, fetchCardAnalytics } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

const RATING_LABELS: Record<number, string> = {
  1: "Again",
  2: "Hard",
  3: "Good",
  4: "Easy",
};

interface CardAnalyticsPanelProps {
  cardId: number;
}

function formatReviewDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function CardAnalyticsPanel({ cardId }: CardAnalyticsPanelProps) {
  const [open, setOpen] = useState(false);
  const [analytics, setAnalytics] = useState<CardAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setAnalytics(null);
    setError(null);
    if (!open) return;

    let cancelled = false;
    setLoading(true);
    void fetchCardAnalytics(cardId)
      .then((data) => {
        if (!cancelled) setAnalytics(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load card stats");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [cardId, open]);

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs">
          Card stats
          <ChevronDown
            className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")}
          />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 rounded-lg border bg-card p-4 text-sm">
        {loading ? (
          <p className="text-muted-foreground">Loading card stats…</p>
        ) : error ? (
          <p className="text-destructive">{error}</p>
        ) : analytics ? (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <p className="text-xs text-muted-foreground">Reps</p>
                <p className="font-medium">{analytics.reps}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Lapses</p>
                <p className="font-medium">{analytics.lapses}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Due</p>
                <p className="font-medium">
                  {analytics.due ? formatReviewDate(analytics.due) : "—"}
                </p>
              </div>
            </div>

            {analytics.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {analytics.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            {analytics.reviews.length > 0 ? (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">
                  Recent reviews
                </p>
                <ul className="space-y-1.5">
                  {analytics.reviews.slice(0, 5).map((review, index) => (
                    <li
                      key={`${review.reviewed_at}-${index}`}
                      className="flex items-center justify-between gap-2 text-xs"
                    >
                      <span>
                        {RATING_LABELS[review.rating] ?? `Rating ${review.rating}`}
                        {review.state ? ` · ${review.state}` : ""}
                      </span>
                      <span className="text-muted-foreground">
                        {formatReviewDate(review.reviewed_at)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No reviews yet.</p>
            )}
          </div>
        ) : null}
      </CollapsibleContent>
    </Collapsible>
  );
}
