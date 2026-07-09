import {
  CartesianGrid,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts";
import type { RetrievabilityPoint } from "@/api";
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
import { retrievabilityChartConfig } from "@/lib/chart-theme";

interface RetrievabilityChartProps {
  data: RetrievabilityPoint[];
}

export function RetrievabilityChart({ data }: RetrievabilityChartProps) {
  const chartData = data.map((item) => ({
    ...item,
    avg_pct: Math.round(item.avg_retrievability * 100),
  }));
  const hasData = chartData.length > 0;

  if (!hasData) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>FSRS retrievability</CardTitle>
        <CardDescription>Average memory strength at review time</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={retrievabilityChartConfig} className="h-[240px] w-full">
          <LineChart data={chartData} margin={{ left: 0, right: 8, top: 8 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
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
                  formatter={(value) => [`${value}%`, "Retrievability"]}
                />
              }
            />
            <Line
              type="monotone"
              dataKey="avg_pct"
              stroke="var(--color-avg_retrievability)"
              strokeWidth={2}
              dot={{ r: 2 }}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
