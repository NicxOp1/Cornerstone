"use client";

import { useState } from "react";
import { ChartTooltip } from "@/components/ui/ChartTooltip";

interface StackedBarDatum {
  date: string;
  label: string;
  fail: number;
  success: number;
  total: number;
}

interface TooltipState {
  title: string;
  rows: Array<{ label: string; value: string }>;
  x: number;
  y: number;
}

interface StackedBarsProps {
  data: StackedBarDatum[];
}

export function StackedBars({ data }: StackedBarsProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  if (data.length === 0) {
    return null;
  }

  const width = 760;
  const height = 280;
  const padding = { top: 16, right: 18, bottom: 42, left: 56 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const step = innerWidth / data.length;
  const barWidth = Math.max(12, step * 0.72);
  const maxTotal = Math.max(...data.map((entry) => entry.total), 1);
  const labelEvery = data.length > 10 ? Math.ceil(data.length / 7) : 1;
  const yTicks = Array.from({ length: 4 }, (_, index) => {
    const ratio = index / 3;
    return Math.round((maxTotal - maxTotal * ratio) * 10) / 10;
  });

  return (
    <div className="relative overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[280px] min-w-[640px] w-full"
        onMouseLeave={() => setTooltip(null)}
      >
        {yTicks.map((tick, index) => {
          const y = padding.top + innerHeight - (tick / maxTotal) * innerHeight;

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
              <text
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                className="fill-ink-soft text-[11px] font-medium"
              >
                {tick}
              </text>
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

        {data.map((entry, index) => {
          const x = padding.left + step * index + (step - barWidth) / 2;
          const failHeight = (entry.fail / maxTotal) * innerHeight;
          const successHeight = (entry.success / maxTotal) * innerHeight;
          const failY = padding.top + innerHeight - failHeight;
          const successY = failY - successHeight;

          return (
            <g key={entry.date}>
              <rect
                x={x}
                y={failY}
                width={barWidth}
                height={Math.max(failHeight, 3)}
                rx={barWidth / 3}
                fill="rgb(var(--bad))"
                fillOpacity="0.76"
              />
              <rect
                x={x}
                y={successY}
                width={barWidth}
                height={Math.max(successHeight, 3)}
                rx={barWidth / 3}
                fill="rgb(var(--good))"
              />
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

                  setTooltip({
                    title: entry.label,
                    rows: [
                      { label: "Successful", value: String(entry.success) },
                      { label: "Unresolved", value: String(entry.fail) },
                      { label: "Total", value: String(entry.total) }
                    ],
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
