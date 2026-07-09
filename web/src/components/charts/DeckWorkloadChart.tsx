import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import type { DeckWorkload } from "@/api";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { deckChartConfig } from "@/lib/chart-theme";

interface DeckWorkloadChartProps {
  data: DeckWorkload[];
}

export function DeckWorkloadChart({ data }: DeckWorkloadChartProps) {
  const chartData = data.slice(0, 10).map((item) => ({
    label: item.label,
    due: item.due,
    caught_up: Math.max(0, item.total - item.due),
  }));

  const hasData = chartData.some((d) => d.due > 0 || d.caught_up > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Deck workload</CardTitle>
        <CardDescription>Due vs caught-up cards by module</CardDescription>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            Import decks to see workload breakdown.
          </p>
        ) : (
          <ChartContainer config={deckChartConfig} className="h-[320px] w-full">
            <BarChart data={chartData} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                interval={0}
                angle={-20}
                textAnchor="end"
                height={60}
              />
              <YAxis tickLine={false} axisLine={false} width={32} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar
                dataKey="caught_up"
                stackId="a"
                fill="var(--color-caught_up)"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="due"
                stackId="a"
                fill="var(--color-due)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
