import { Cell, Pie, PieChart } from "recharts";
import type { RatingBucket } from "@/api";
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
import { RATING_COLORS, ratingChartConfig } from "@/lib/chart-theme";

interface RatingDonutChartProps {
  data: RatingBucket[];
}

export function RatingDonutChart({ data }: RatingDonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rating mix</CardTitle>
        <CardDescription>How you rated cards recently</CardDescription>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">
            Review cards to see rating distribution.
          </p>
        ) : (
          <div className="relative">
            <ChartContainer config={ratingChartConfig} className="mx-auto h-[280px] w-full max-w-[320px]">
              <PieChart>
                <ChartTooltip content={<ChartTooltipContent hideLabel />} />
                <Pie
                  data={data}
                  dataKey="count"
                  nameKey="label"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {data.map((entry) => (
                    <Cell
                      key={entry.rating}
                      fill={RATING_COLORS[entry.label] ?? "hsl(217 91% 60%)"}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ChartContainer>
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-3xl font-bold">{total}</p>
                <p className="text-xs text-muted-foreground">reviews</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
