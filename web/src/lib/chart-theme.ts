import type { ChartConfig } from "@/components/ui/chart";

export const activityChartConfig: ChartConfig = {
  reviews: { label: "Reviews", color: "hsl(217 91% 60%)" },
  good: { label: "Good+", color: "hsl(142 71% 45%)" },
  again: { label: "Again", color: "hsl(0 84% 60%)" },
};

export const retentionChartConfig: ChartConfig = {
  retention_pct: { label: "Retention %", color: "hsl(217 91% 60%)" },
};

export const ratingChartConfig: ChartConfig = {
  Again: { label: "Again", color: "hsl(0 84% 60%)" },
  Hard: { label: "Hard", color: "hsl(38 92% 50%)" },
  Good: { label: "Good", color: "hsl(142 71% 45%)" },
  Easy: { label: "Easy", color: "hsl(187 85% 43%)" },
};

export const masteryChartConfig: ChartConfig = {
  mastery: { label: "Mastery %", color: "hsl(217 91% 60%)" },
};

export const deckChartConfig: ChartConfig = {
  due: { label: "Due", color: "hsl(0 84% 60%)" },
  caught_up: { label: "Caught up", color: "hsl(142 71% 45%)" },
};

export const retrievabilityChartConfig: ChartConfig = {
  avg_retrievability: { label: "Retrievability", color: "hsl(262 83% 58%)" },
};

export const RATING_COLORS: Record<string, string> = {
  Again: "hsl(0 84% 60%)",
  Hard: "hsl(38 92% 50%)",
  Good: "hsl(142 71% 45%)",
  Easy: "hsl(187 85% 43%)",
};
