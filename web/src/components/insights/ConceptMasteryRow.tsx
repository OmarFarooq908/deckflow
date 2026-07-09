import { Link } from "react-router-dom";
import type { ConceptMastery } from "@/api";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { reviewUrl } from "@/lib/format";

interface ConceptMasteryRowProps {
  concept: ConceptMastery;
}

export function ConceptMasteryRow({ concept }: ConceptMasteryRowProps) {
  return (
    <div className="space-y-2 rounded-lg border bg-card/40 p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center justify-between gap-3 text-sm sm:justify-start">
            <span className="font-medium">{concept.label || concept.slug}</span>
            <span className="text-muted-foreground">
              {concept.mastery_score.toFixed(0)}% mastery
            </span>
          </div>
          <Progress value={concept.mastery_score} className="h-2" />
        </div>
        <Button asChild variant="outline" size="sm" className="shrink-0">
          <Link to={reviewUrl(undefined, concept.slug)}>Review</Link>
        </Button>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Retention (7d)</dt>
          <dd className="font-medium">{concept.retention_7d.toFixed(0)}%</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Retention (30d)</dt>
          <dd className="font-medium">{concept.retention_30d.toFixed(0)}%</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Weakness</dt>
          <dd className="font-medium">{concept.weakness_score.toFixed(0)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Reviews</dt>
          <dd className="font-medium">{concept.reviews_count}</dd>
        </div>
      </dl>
    </div>
  );
}
