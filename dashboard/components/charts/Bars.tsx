"use client";

import { useState } from "react";
import { ChartTooltip } from "@/components/ui/ChartTooltip";
import { formatCurrency, formatDuration, formatNumber, formatPercent } from "@/lib/utils/format";

type BarFormat = "currency" | "duration" | "number" | "percent";

export interface BarSeries {
  key: string;
  label: string;
  colorVar: string;
}

export interface BarDatum {
  label: string;
  values: Record<string, number>;
}

interface BarsProps {
  data: BarDatum[];
  series: BarSeries[];
  format?: BarFormat;
}

interface TooltipState {
  title: string;
  rows: Array<{ label: string; value: string }>;
  x: number;
  y: number;
}

function formatValue(value: number, format: BarFormat): string {
  switch (format) {
    case "currency":
      return formatCurrency(value);
    case "duration":
      return formatDuration(value);
    case "percent":
      return formatPercent(value);
    case "number":
    default:
      return formatNumber(value);
  }
}

export function Bars({ data, series, format = "number" }: BarsProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  if (data.length === 0) {
    return null;
  }

  const width = 760;
  const height = 280;
  const padding = { top: 12, right: 16, bottom: 42, left: 16 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const step = innerWidth / data.length;
  const barWidth = Math.max(10, step * 0.66);
  const totals = data.map((entry) => series.reduce((sum, item) => sum + (entry.values[item.key] ?? 0), 0));
  const maxTotal = Math.max(...totals, 1);
  const labelEvery = data.length > 10 ? Math.ceil(data.length / 7) : 1;

  return (
    <div className="relative overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[280px] min-w-[560px] w-full"
        onMouseLeave={() => setTooltip(null)}
      >
        <line
          x1={padding.left}
          y1={padding.top + innerHeight}
          x2={width - padding.right}
          y2={padding.top + innerHeight}
          className="stroke-line"
          strokeWidth="1"
        />

        {data.map((entry, index) => {
          const x = padding.left + step * index + (step - barWidth) / 2;
          let cursorY = padding.top + innerHeight;
          const total = totals[index];

          return (
            <g key={entry.label}>
              {series.map((item) => {
                const value = entry.values[item.key] ?? 0;
                const barHeight = (value / maxTotal) * innerHeight;
                cursorY -= barHeight;

                return value > 0 ? (
                  <rect
                    key={item.key}
                    x={x}
                    y={cursorY}
                    width={barWidth}
                    height={Math.max(barHeight, 2)}
                    rx={Math.min(barWidth / 3, 6)}
                    fill={`rgb(var(--${item.colorVar}))`}
                  />
                ) : null;
              })}
              <rect
                x={x - 4}
                y={padding.top}
                width={barWidth + 8}
                height={innerHeight + padding.bottom}
                fill="transparent"
                onMouseMove={(event) => {
                  const bounds = event.currentTarget.ownerSVGElement?.getBoundingClientRect();

                  if (!bounds) {
                    return;
                  }

                  const rows = series.map((item) => ({
                    label: item.label,
                    value: formatValue(entry.values[item.key] ?? 0, format)
                  }));

                  setTooltip({
                    title: entry.label,
                    rows:
                      series.length > 1
                        ? [...rows, { label: "Total", value: formatValue(total, format) }]
                        : rows,
                    x: event.clientX - bounds.left,
                    y: event.clientY - bounds.top
                  });
                }}
              />
              {index % labelEvery === 0 ? (
                <text
                  x={x + barWidth / 2}
                  y={height - 12}
                  textAnchor="middle"
                  className="fill-ink-soft text-[11px] font-medium"
                >
                  {entry.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>

      <ChartTooltip
        title={tooltip?.title ?? ""}
        rows={tooltip?.rows ?? []}
        x={tooltip?.x ?? 0}
        y={tooltip?.y ?? 0}
        visible={tooltip !== null}
      />
    </div>
  );
}
