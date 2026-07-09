"use client";

import { useId, useState } from "react";
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
  fillVar?: string;
  showArea?: boolean;
  showYAxis?: boolean;
  strokeVar?: string;
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

export function AreaTrend({
  data,
  format = "number",
  fillVar = "navy-2",
  showArea = true,
  showYAxis = true,
  strokeVar = "navy-2"
}: AreaTrendProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const gradientId = useId().replace(/:/g, "");

  if (data.length === 0) {
    return null;
  }

  const width = 760;
  const height = 290;
  const padding = { top: 18, right: 18, bottom: 42, left: showYAxis ? 64 : 18 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...data.map((point) => point.value), 1);
  const minValue = Math.min(...data.map((point) => point.value), 0);
  const range = maxValue - minValue || 1;
  const labelEvery = data.length > 10 ? Math.ceil(data.length / 7) : 1;
  const yTicks = Array.from({ length: 4 }, (_, index) => {
    const ratio = index / 3;
    return minValue + (maxValue - minValue) * (1 - ratio);
  });

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
          <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={`rgb(var(--${fillVar}))`} stopOpacity="0.34" />
            <stop offset="100%" stopColor={`rgb(var(--${fillVar}))`} stopOpacity="0.03" />
          </linearGradient>
        </defs>

        {yTicks.map((tick, index) => {
          const y = padding.top + innerHeight - ((tick - minValue) / range) * innerHeight;

          return (
            <g key={`tick-${index}`}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="rgb(var(--line))"
                strokeDasharray="4 6"
                strokeWidth="1"
              />
              {showYAxis ? (
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-ink-soft text-[11px] font-medium"
                >
                  {formatValue(tick, format)}
                </text>
              ) : null}
            </g>
          );
        })}

        <line
          x1={padding.left}
          y1={padding.top + innerHeight}
          x2={width - padding.right}
          y2={padding.top + innerHeight}
          className="stroke-line"
          strokeWidth="1"
        />

        {showArea ? <path d={areaPath} fill={`url(#${gradientId})`} /> : null}
        <path d={linePath} fill="none" stroke={`rgb(var(--${strokeVar}))`} strokeWidth="3" />

        {points.map((point, index) => (
          <g key={point.date}>
            <circle
              cx={point.x}
              cy={point.y}
              r={index === points.length - 1 ? 6 : 4}
              fill={index === points.length - 1 ? "rgb(var(--accent))" : `rgb(var(--${strokeVar}))`}
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
