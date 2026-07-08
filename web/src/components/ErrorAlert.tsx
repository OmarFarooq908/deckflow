import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { formatApiError } from "@/lib/format";

interface ErrorAlertProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
}

export function ErrorAlert({
  error,
  onRetry,
  title = "Something went wrong",
}: ErrorAlertProps) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>{formatApiError(error)}</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            Try again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
