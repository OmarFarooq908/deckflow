import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AnalyticsDashboard,
  ConceptMastery,
  Deck,
  StudyPlanItem,
  WeakSpot,
  fetchAnalyticsDashboard,
  fetchConceptMastery,
  fetchDecks,
  fetchStudyPlan,
  fetchWeakSpots,
} from "@/api";
import { DueBadge } from "@/components/DueBadge";
import { ErrorAlert } from "@/components/ErrorAlert";
import { InsightsDashboard } from "@/components/insights/InsightsDashboard";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { reviewUrl } from "@/lib/format";

export function StatsPage() {
  const [dashboard, setDashboard] = useState<AnalyticsDashboard | null>(null);
  const [concepts, setConcepts] = useState<ConceptMastery[]>([]);
  const [weakSpots, setWeakSpots] = useState<WeakSpot[]>([]);
  const [plan, setPlan] = useState<StudyPlanItem[]>([]);
  const [decks, setDecks] = useState<Deck[]>([]);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    Promise.all([
      fetchAnalyticsDashboard(),
      fetchConceptMastery(),
      fetchWeakSpots(),
      fetchStudyPlan(),
      fetchDecks(),
    ])
      .then(([dashboardData, conceptsData, spotsData, planData, deckData]) => {
        setDashboard(dashboardData);
        setConcepts(conceptsData);
        setWeakSpots(spotsData);
        setPlan(planData);
        setDecks(deckData);
      })
      .catch((err: Error) => setError(err));
  }, []);

  if (error) {
    return <ErrorAlert error={error} title="Could not load insights" />;
  }

  if (!dashboard) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title="Insights"
        subtitle="Track retention, mastery, and what to study next"
        action={
          <Button asChild>
            <Link to="/review">Start review</Link>
          </Button>
        }
      />

      <Tabs defaultValue="overview">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="plan">Plan</TabsTrigger>
          <TabsTrigger value="mastery">Mastery</TabsTrigger>
          <TabsTrigger value="decks">Decks</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <InsightsDashboard dashboard={dashboard} />
        </TabsContent>

        <TabsContent value="plan" className="space-y-3">
          {plan.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No cards queued for today.
            </p>
          ) : (
            plan.map((item) => (
              <Card key={item.card_id} className="transition-colors hover:bg-accent/30">
                <CardContent className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">{item.front_preview}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.deck_path.split("::").pop()} · {item.reason}
                    </p>
                  </div>
                  <Button asChild variant="secondary" size="sm">
                    <Link to={reviewUrl(item.deck_path)}>Review</Link>
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="mastery" className="space-y-4">
          {weakSpots.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium">Weak spots</h3>
              {weakSpots.map((spot) => (
                <Alert key={spot.concept_slug} variant="destructive">
                  <AlertTitle>{spot.concept_label}</AlertTitle>
                  <AlertDescription className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <span>{spot.message}</span>
                    <Button asChild variant="outline" size="sm">
                      <Link to={reviewUrl(undefined, spot.concept_slug)}>
                        Review topic
                      </Link>
                    </Button>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}

          {concepts.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Review cards to build mastery data.
            </p>
          ) : (
            <div className="space-y-3">
              {concepts.slice(0, 16).map((concept) => (
                <div key={concept.concept_id} className="space-y-1.5">
                  <div className="flex justify-between text-sm">
                    <span>{concept.label || concept.slug}</span>
                    <span className="text-muted-foreground">
                      {concept.mastery_score.toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={concept.mastery_score} className="h-2" />
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="decks" className="space-y-2">
          {decks.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No decks imported yet.
            </p>
          ) : (
            decks.map((deck) => (
              <Card key={deck.id}>
                <CardContent className="flex items-center justify-between gap-3 p-4">
                  <Button asChild variant="link" className="h-auto p-0 text-left">
                    <Link to={reviewUrl(deck.path)}>{deck.path}</Link>
                  </Button>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <DueBadge count={deck.due_count} />
                    <span>{deck.card_count} total</span>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
