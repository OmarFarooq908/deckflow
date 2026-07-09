import type { CollectionSummary } from "@/api";
import { DueBadge } from "@/components/DueBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface CollectionSummaryCardProps {
  collection: CollectionSummary;
}

export function CollectionSummaryCard({ collection }: CollectionSummaryCardProps) {
  const progressPct =
    collection.card_count > 0
      ? Math.round(
          ((collection.card_count - collection.due_count) / collection.card_count) * 100,
        )
      : 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="text-base font-medium">{collection.title}</CardTitle>
            {collection.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {collection.description}
              </p>
            )}
          </div>
          <DueBadge count={collection.due_count} />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {collection.due_count} due · {collection.card_count} total cards
        </p>
        <Progress value={progressPct} className="mt-3 h-2" />
        <p className="mt-2 text-xs text-muted-foreground">
          {progressPct}% not due right now
        </p>
      </CardContent>
    </Card>
  );
}
