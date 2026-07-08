import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface DueBadgeProps {
  count: number;
  className?: string;
}

export function DueBadge({ count, className }: DueBadgeProps) {
  if (count <= 0) return null;
  return (
    <Badge variant="destructive" className={cn("font-medium", className)}>
      {count} due
    </Badge>
  );
}
