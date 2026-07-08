import { type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Link } from "react-router-dom";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  actionTo?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  actionTo,
}: EmptyStateProps) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
        {icon && <div className="text-muted-foreground">{icon}</div>}
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
        {actionLabel && actionTo && (
          <Button asChild>
            <Link to={actionTo}>{actionLabel}</Link>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
