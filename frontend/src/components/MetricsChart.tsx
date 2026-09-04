import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MetricSnapshotRead } from "../api/types";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

interface MetricsChartProps {
  data: MetricSnapshotRead[];
}

function MetricsChart({ data }: MetricsChartProps) {
  const chartData = data.map((point) => ({
    time: formatTime(point.timestamp),
    errorRatePct: Number((point.error_rate * 100).toFixed(2)),
    latencyP95: Math.round(point.latency_p95_ms),
  }));

  return (
    <div className="metrics-chart-grid">
      <div className="metrics-chart">
        <div className="metrics-chart-title">Error rate (%)</div>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} minTickGap={30} />
            <YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip
              contentStyle={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey="errorRatePct"
              stroke="var(--color-danger)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="metrics-chart">
        <div className="metrics-chart-title">P95 latency (ms)</div>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} minTickGap={30} />
            <YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip
              contentStyle={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey="latencyP95"
              stroke="var(--color-info)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default MetricsChart;
