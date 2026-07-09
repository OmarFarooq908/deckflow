import type { AnalyticsDashboard } from "@/api";
import { ActivityAreaChart } from "@/components/charts/ActivityAreaChart";
import { DeckWorkloadChart } from "@/components/charts/DeckWorkloadChart";
import { MasteryBarChart } from "@/components/charts/MasteryBarChart";
import { RatingDonutChart } from "@/components/charts/RatingDonutChart";
import { RetentionLineChart } from "@/components/charts/RetentionLineChart";
import { RetrievabilityChart } from "@/components/charts/RetrievabilityChart";
import { StatCard } from "@/components/StatCard";
import { LoadingState } from "@/components/LoadingState";

interface InsightsDashboardProps {
  dashboard: AnalyticsDashboard | null;
  loading?: boolean;
}

export function InsightsDashboard({ dashboard, loading }: InsightsDashboardProps) {
  if (loading || !dashboard) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <LoadingState key={i} variant="card" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <LoadingState variant="card" />
          <LoadingState variant="card" />
        </div>
        <LoadingState variant="card" />
        <div className="grid gap-4 lg:grid-cols-2">
          <LoadingState variant="card" />
          <LoadingState variant="card" />
        </div>
        <LoadingState variant="card" />
      </div>
    );
  }

  const { overview } = dashboard;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Retention (7d)" value={`${overview.retention_7d}%`} />
        <StatCard label="Retention (30d)" value={`${overview.retention_30d}%`} />
        <StatCard label="Cards/day (7d)" value={overview.cards_per_day_7d} />
        <StatCard label="Avg mastery" value={`${overview.avg_mastery}%`} />
        <StatCard label="Due today" value={overview.due_today} />
        <StatCard label="Streak" value={`${overview.streak_days}d`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ActivityAreaChart data={dashboard.activity} />
        <RatingDonutChart data={dashboard.ratings} />
      </div>

      <RetentionLineChart data={dashboard.retention_trend} />

      <div className="grid gap-4 lg:grid-cols-2">
        <MasteryBarChart
          title="Strongest topics"
          description="Highest mastery scores"
          data={dashboard.mastery_top}
          emptyMessage="Review cards to see mastery data."
        />
        <MasteryBarChart
          title="Weakest topics"
          description="Topics that need more practice"
          data={dashboard.mastery_bottom}
          emptyMessage="Review cards to identify weak spots."
        />
      </div>

      <DeckWorkloadChart data={dashboard.deck_workload} />

      <RetrievabilityChart data={dashboard.retrievability_trend} />
    </div>
  );
}
