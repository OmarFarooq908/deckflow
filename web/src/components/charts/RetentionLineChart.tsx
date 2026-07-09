import {
  CartesianGrid,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts";
import type { RetentionTrendPoint } from "@/api";
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
import { retentionChartConfig } from "@/lib/chart-theme";

interface RetentionLineChartProps {
  data: RetentionTrendPoint[];
}

export function RetentionLineChart({ data }: RetentionLineChartProps) {
  const hasData = data.some((d) => d.reviews > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Retention trend</CardTitle>
        <CardDescription>Weekly recall rate (Good+ ratings)</CardDescription>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            Review cards to see retention trends.
          </p>
        ) : (
          <ChartContainer config={retentionChartConfig} className="h-[280px] w-full">
            <LineChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="period"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(value: string) => value.slice(5)}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                width={36}
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value) => [`${value}%`, "Retention"]}
                  />
                }
              />
              <Line
                type="monotone"
                dataKey="retention_pct"
                stroke="var(--color-retention_pct)"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
