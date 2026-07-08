import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { fetchLibrary, type LearningLibrary } from "@/api";
import { ErrorAlert } from "@/components/ErrorAlert";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { LibraryTree } from "@/components/library/LibraryTree";
import { TrackCard } from "@/components/library/TrackCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function LibraryPage() {
  const [library, setLibrary] = useState<LearningLibrary | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetchLibrary()
      .then(setLibrary)
      .catch((err: Error) => setError(err));
  }, []);

  if (error) {
    return <ErrorAlert error={error} title="Could not load library" />;
  }

  if (!library) {
    return <LoadingState />;
  }

  const collection = library.collection;
  const progressPct =
    collection && collection.card_count > 0
      ? Math.round(
          ((collection.card_count - collection.due_count) / collection.card_count) *
            100,
        )
      : 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title={collection?.title ?? "Learning library"}
        subtitle="Browse modules, topics, and study tracks"
        action={
          <Button asChild>
            <Link to="/review">Global review</Link>
          </Button>
        }
      />

      {collection && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium">
              {collection.due_count} due · {collection.card_count} total cards
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={progressPct} className="h-2" />
            <p className="mt-2 text-xs text-muted-foreground">
              {progressPct}% of cards not due right now
            </p>
          </CardContent>
        </Card>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Filter modules and topics..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      <Tabs defaultValue="modules">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="modules">Modules</TabsTrigger>
          <TabsTrigger value="topics">Topics</TabsTrigger>
        </TabsList>
        <TabsContent value="modules">
          {library.modules.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Import a deck to see modules.
            </p>
          ) : (
            <LibraryTree
              nodes={library.modules}
              filter={filter}
              defaultExpanded
            />
          )}
        </TabsContent>
        <TabsContent value="topics">
          {library.topics.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Review cards to build topic mastery.
            </p>
          ) : (
            <LibraryTree
              nodes={library.topics}
              showMastery
              filter={filter}
              defaultExpanded
            />
          )}
        </TabsContent>
      </Tabs>

      {library.tracks.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Study tracks</h2>
          <div className="grid gap-3">
            {library.tracks.map((track) => (
              <TrackCard key={track.id} track={track} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
