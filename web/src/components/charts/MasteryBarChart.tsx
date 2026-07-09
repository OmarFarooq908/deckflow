import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import type { ConceptMastery } from "@/api";
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
import { masteryChartConfig } from "@/lib/chart-theme";

interface MasteryBarChartProps {
  title: string;
  description: string;
  data: ConceptMastery[];
  emptyMessage: string;
}

export function MasteryBarChart({
  title,
  description,
  data,
  emptyMessage,
}: MasteryBarChartProps) {
  const chartData = data.map((item) => ({
    label: item.label || item.slug.split("::").pop() || item.slug,
    mastery: Math.round(item.mastery_score),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            {emptyMessage}
          </p>
        ) : (
          <ChartContainer config={masteryChartConfig} className="h-[280px] w-full">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ left: 8, right: 16, top: 8 }}
            >
              <CartesianGrid horizontal={false} strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <YAxis
                type="category"
                dataKey="label"
                width={100}
                tickLine={false}
                axisLine={false}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value) => [`${value}%`, "Mastery"]}
                  />
                }
              />
              <Bar dataKey="mastery" fill="var(--color-mastery)" radius={4} />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
