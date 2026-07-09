import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import type { ActivityPoint } from "@/api";
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
import { activityChartConfig } from "@/lib/chart-theme";

interface ActivityAreaChartProps {
  data: ActivityPoint[];
}

export function ActivityAreaChart({ data }: ActivityAreaChartProps) {
  const hasData = data.some((d) => d.reviews > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review activity</CardTitle>
        <CardDescription>Daily reviews over the last 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            Review cards to see activity trends.
          </p>
        ) : (
          <ChartContainer config={activityChartConfig} className="h-[280px] w-full">
            <AreaChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(value: string) => value.slice(5)}
              />
              <YAxis tickLine={false} axisLine={false} width={32} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Area
                type="monotone"
                dataKey="good"
                stackId="1"
                stroke="var(--color-good)"
                fill="var(--color-good)"
                fillOpacity={0.35}
              />
              <Area
                type="monotone"
                dataKey="again"
                stackId="1"
                stroke="var(--color-again)"
                fill="var(--color-again)"
                fillOpacity={0.35}
              />
            </AreaChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
