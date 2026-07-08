import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Upload } from "lucide-react";
import { importDeck } from "@/api";
import { EmptyState } from "@/components/EmptyState";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useStatsContext } from "@/hooks/useStatsContext";
import { greetingForHour } from "@/lib/format";

export function HomePage() {
  const { stats, loading, refresh } = useStatsContext();
  const [importPath, setImportPath] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  useEffect(() => {
    if (stats?.last_import_path) {
      setImportPath(stats.last_import_path);
    }
  }, [stats?.last_import_path]);

  async function handleImport() {
    setError(null);
    setMessage(null);
    try {
      const result = await importDeck(importPath);
      setMessage(`Imported ${result.imported} cards from ${result.path}`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    }
  }

  if (loading) {
    return <LoadingState />;
  }

  const greeting = greetingForHour(new Date().getHours());
  const hasCards = (stats?.total_cards ?? 0) > 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title={greeting}
        subtitle={
          hasCards
            ? `${stats?.due_today ?? 0} cards due today`
            : "Import a deck to start your learning ritual"
        }
      />

      {!hasCards ? (
        <EmptyState
          icon={<BookOpen className="h-10 w-10" />}
          title="No decks yet"
          description="Import the example project or your own deck to begin reviewing."
          actionLabel="Browse library"
          actionTo="/library"
        />
      ) : (
        <Card className="border-primary/20 bg-gradient-to-br from-card to-primary/5">
          <CardHeader>
            <CardTitle className="text-4xl font-bold tracking-tight">
              {stats?.due_today ?? 0}
            </CardTitle>
            <CardDescription>cards ready for review</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/review">Start review</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link to="/library">Choose what to study</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {hasCards && stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Streak" value={`${stats.streak_days}d`} />
          <StatCard label="Retention" value={`${stats.retention_pct}%`} />
          <StatCard label="Reviewed today" value={stats.reviewed_today} />
          <StatCard label="New cards" value={stats.new_cards} />
        </div>
      )}

      <Collapsible open={importOpen} onOpenChange={setImportOpen}>
        <Card>
          <CollapsibleTrigger asChild>
            <button
              type="button"
              className="flex w-full items-center justify-between p-6 text-left"
            >
              <div className="flex items-center gap-2">
                <Upload className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Import deck</span>
              </div>
              <span className="text-sm text-muted-foreground">
                {importOpen ? "Hide" : "Advanced"}
              </span>
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <Separator />
            <CardContent className="space-y-4 pt-6">
              <p className="text-sm text-muted-foreground">
                Path to a v2 project, collection folder, or markdown deck file.
              </p>
              <Input
                value={importPath}
                onChange={(e) => setImportPath(e.target.value)}
                placeholder="/absolute/path/to/deck-project"
              />
              <Button variant="secondary" onClick={() => void handleImport()}>
                Import
              </Button>
              {message && <p className="text-sm text-green-400">{message}</p>}
              {error && <ErrorAlert error={error} />}
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>
    </div>
  );
}
