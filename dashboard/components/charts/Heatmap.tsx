"use client";

import { useState } from "react";
import { ChartTooltip } from "@/components/ui/ChartTooltip";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface TooltipState {
  title: string;
  rows: Array<{ label: string; value: string }>;
  x: number;
  y: number;
}

interface HeatmapProps {
  matrix: number[][];
}

export function Heatmap({ matrix }: HeatmapProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const width = 760;
  const height = 280;
  const padding = { top: 20, right: 18, bottom: 34, left: 64 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const columns = 24;
  const rows = 7;
  const cellWidth = innerWidth / columns;
  const cellHeight = innerHeight / rows;
  const maxValue = Math.max(...matrix.flat(), 0);

  return (
    <div className="relative overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[280px] min-w-[680px] w-full"
        onMouseLeave={() => setTooltip(null)}
      >
        {WEEKDAY_LABELS.map((label, rowIndex) => (
          <text
            key={label}
            x={padding.left - 14}
            y={padding.top + rowIndex * cellHeight + cellHeight / 2 + 4}
            textAnchor="end"
            className="fill-ink-soft text-[11px] font-medium"
          >
            {label}
          </text>
        ))}

        {[0, 6, 12, 18, 23].map((hour) => (
          <text
            key={hour}
            x={padding.left + hour * cellWidth + cellWidth / 2}
            y={height - 10}
            textAnchor="middle"
            className="fill-ink-soft text-[11px] font-medium"
          >
            {String(hour).padStart(2, "0")}
          </text>
        ))}

        {matrix.map((row, rowIndex) =>
          row.map((value, columnIndex) => {
            const ratio = maxValue === 0 ? 0 : value / maxValue;
            const x = padding.left + columnIndex * cellWidth;
            const y = padding.top + rowIndex * cellHeight;

            return (
              <g key={`${rowIndex}-${columnIndex}`}>
                <rect
                  x={x + 2}
                  y={y + 2}
                  width={cellWidth - 4}
                  height={cellHeight - 4}
                  rx="8"
                  fill="rgb(var(--navy))"
                  fillOpacity={0.12 + ratio * 0.88}
                  stroke={value > 0 && value === maxValue ? "rgb(var(--accent))" : "transparent"}
                  strokeWidth={value > 0 && value === maxValue ? 2 : 0}
                />
                <rect
                  x={x}
                  y={y}
                  width={cellWidth}
                  height={cellHeight}
                  fill="transparent"
                  onMouseMove={(event) => {
                    const bounds = event.currentTarget.ownerSVGElement?.getBoundingClientRect();

                    if (!bounds) {
                      return;
                    }

                    setTooltip({
                      title: `${WEEKDAY_LABELS[rowIndex]} / ${String(columnIndex).padStart(2, "0")}:00-${String((columnIndex + 1) % 24).padStart(2, "0")}:00`,
                      rows: [{ label: "Calls", value: String(value) }],
                      x: event.clientX - bounds.left,
                      y: event.clientY - bounds.top
                    });
                  }}
                />
              </g>
            );
          })
        )}
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
