"use client";

import { useState } from "react";
import { ChartTooltip } from "@/components/ui/ChartTooltip";
import { formatCurrency, formatDuration, formatNumber, formatPercent } from "@/lib/utils/format";

type FormatMode = "currency" | "duration" | "number" | "percent";

interface AreaTrendDatum {
  date: string;
  label: string;
  value: number;
}

interface TooltipState {
  title: string;
  rows: Array<{ label: string; value: string }>;
  x: number;
  y: number;
}

interface AreaTrendProps {
  data: AreaTrendDatum[];
  format?: FormatMode;
}

function formatValue(value: number, format: FormatMode): string {
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

export function AreaTrend({ data, format = "number" }: AreaTrendProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  if (data.length === 0) {
    return null;
  }

  const width = 760;
  const height = 290;
  const padding = { top: 18, right: 16, bottom: 42, left: 16 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...data.map((point) => point.value), 1);
  const minValue = Math.min(...data.map((point) => point.value), 0);
  const range = maxValue - minValue || 1;
  const labelEvery = data.length > 10 ? Math.ceil(data.length / 7) : 1;

  const points = data.map((point, index) => {
    const x = data.length === 1 ? padding.left + innerWidth / 2 : padding.left + (index / (data.length - 1)) * innerWidth;
    const y = padding.top + innerHeight - ((point.value - minValue) / range) * innerHeight;
    return { ...point, x, y };
  });

  const linePath = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + innerHeight} L ${points[0].x} ${padding.top + innerHeight} Z`;

  return (
    <div className="relative overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[290px] min-w-[640px] w-full"
        onMouseLeave={() => setTooltip(null)}
      >
        <defs>
          <linearGradient id="overview-area-fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="rgb(var(--navy))" stopOpacity="0.3" />
            <stop offset="100%" stopColor="rgb(var(--navy))" stopOpacity="0.03" />
          </linearGradient>
        </defs>

        <line
          x1={padding.left}
          y1={padding.top + innerHeight}
          x2={width - padding.right}
          y2={padding.top + innerHeight}
          className="stroke-line"
          strokeWidth="1"
        />

        <path d={areaPath} fill="url(#overview-area-fill)" />
        <path d={linePath} fill="none" stroke="rgb(var(--navy))" strokeWidth="3" />

        {points.map((point, index) => (
          <g key={point.date}>
            <circle
              cx={point.x}
              cy={point.y}
              r={index === points.length - 1 ? 6 : 4}
              fill={index === points.length - 1 ? "rgb(var(--accent))" : "rgb(var(--navy))"}
              stroke="rgb(var(--card))"
              strokeWidth="2"
            />
            <circle
              cx={point.x}
              cy={point.y}
              r="12"
              fill="transparent"
              onMouseMove={(event) => {
                const bounds = event.currentTarget.ownerSVGElement?.getBoundingClientRect();

                if (!bounds) {
                  return;
                }

                setTooltip({
                  title: point.label,
                  rows: [{ label: "Value", value: formatValue(point.value, format) }],
                  x: event.clientX - bounds.left,
                  y: event.clientY - bounds.top
                });
              }}
            />
            {index % labelEvery === 0 ? (
              <text
                x={point.x}
                y={height - 12}
                textAnchor="middle"
                className="fill-ink-soft text-[11px] font-medium"
              >
                {point.label}
              </text>
            ) : null}
          </g>
        ))}
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
