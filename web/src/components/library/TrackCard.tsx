import { Link } from "react-router-dom";
import type { TrackSummary } from "@/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { reviewUrl } from "@/lib/format";

interface TrackCardProps {
  track: TrackSummary;
}

export function TrackCard({ track }: TrackCardProps) {
  const stepNum = track.current_step + 1;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-base">{track.title}</CardTitle>
            {track.description && (
              <p className="mt-1 text-sm text-muted-foreground">
                {track.description}
              </p>
            )}
          </div>
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            Step {stepNum} of {track.total_steps}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {track.steps.map((step, index) => (
            <div
              key={step.step_index}
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full border text-xs font-medium",
                index === track.current_step
                  ? "border-primary bg-primary text-primary-foreground"
                  : step.completed
                    ? "border-green-500/50 bg-green-500/10 text-green-300"
                    : "border-border text-muted-foreground",
              )}
            >
              {index + 1}
            </div>
          ))}
        </div>
        <Button asChild>
          <Link to={reviewUrl(track.focus_deck_prefix, track.focus_concept_slug)}>
            Continue track
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
