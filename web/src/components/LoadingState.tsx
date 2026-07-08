import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface LoadingStateProps {
  variant?: "page" | "card" | "review";
}

export function LoadingState({ variant = "page" }: LoadingStateProps) {
  if (variant === "review") {
    return (
      <div className="space-y-4 animate-in fade-in duration-300">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64" />
        <Card>
          <CardContent className="space-y-3 p-6">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (variant === "card") {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-56" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-72" />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
      <Skeleton className="h-40 w-full" />
    </div>
  );
}
