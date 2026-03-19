import type {
  StockByLocationData,
  MovementTrendsData,
  ChartDataset,
} from "../types/dashboard.types";

export interface BarChartDatum {
  name: string;
  reserved: number;
  available: number;
}

export function toStockByLocationBarData(
  raw: StockByLocationData,
): BarChartDatum[] {
  return raw.labels.map((label, i) => ({
    name: label,
    reserved: raw.reserved[i] ?? 0,
    available: raw.available[i] ?? 0,
  }));
}

export interface TrendDatum {
  date: string;
  movements: number;
}

export function toMovementTrendData(raw: MovementTrendsData): TrendDatum[] {
  return raw.labels.map((label, i) => ({
    date: label,
    movements: raw.data[i] ?? 0,
  }));
}

export interface PieDatum {
  name: string;
  value: number;
  fill: string;
}

const STATUS_COLORS: Record<string, string> = {
  Draft: "var(--color-chart-1)",
  Confirmed: "var(--color-chart-2)",
  Received: "var(--color-chart-3)",
  Fulfilled: "var(--color-chart-3)",
  Cancelled: "var(--color-chart-4)",
};

export function toPieData(dataset: ChartDataset): PieDatum[] {
  const fallbackColors = [
    "var(--color-chart-1)",
    "var(--color-chart-2)",
    "var(--color-chart-3)",
    "var(--color-chart-4)",
    "var(--color-chart-5)",
  ];

  return dataset.labels.map((label, i) => ({
    name: label,
    value: dataset.data[i] ?? 0,
    fill: STATUS_COLORS[label] ?? fallbackColors[i % fallbackColors.length],
  }));
}

export function formatCompactNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

export function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "$0.00";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(num);
}

export function formatShortDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
