"use client";

import { useState } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatNumber, formatPercent } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type DonutColor = "neg" | "neu" | "pos" | "unk";

const colorMap: Record<DonutColor, string> = {
  neg: "rgb(var(--neg))",
  neu: "rgb(var(--neu))",
  pos: "rgb(var(--pos))",
  unk: "rgb(var(--unk))"
};

interface Segment {
  color: DonutColor;
  label: string;
  value: number;
}

interface DonutProps {
  segments: Segment[];
  totalLabel: string;
}

function polarToCartesian(cx: number, cy: number, radius: number, angle: number) {
  return {
    x: cx + radius * Math.cos(angle),
    y: cy + radius * Math.sin(angle)
  };
}

function describeArc(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= Math.PI ? "0" : "1";
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

export function Donut({ segments, totalLabel }: DonutProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);

  if (total === 0) {
    return (
      <EmptyState
        title="No sentiment data yet"
        description="Sentiment will appear here once synced calls include that signal."
      />
    );
  }

  let angleCursor = -Math.PI / 2;

  return (
    <div className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:items-center">
      <div className="relative mx-auto h-[240px] w-[240px]">
        <svg viewBox="0 0 240 240" className="h-full w-full">
          <circle cx="120" cy="120" r="76" fill="none" stroke="rgb(var(--muted))" strokeWidth="28" />
          {segments.map((segment, index) => {
            const share = segment.value / total;
            const startAngle = angleCursor;
            const endAngle = angleCursor + share * Math.PI * 2;
            angleCursor = endAngle;

            return (
              <path
                key={segment.label}
                d={describeArc(120, 120, activeIndex === index ? 82 : 76, startAngle, endAngle)}
                fill="none"
                stroke={colorMap[segment.color]}
                strokeWidth={activeIndex === index ? 32 : 28}
                strokeLinecap="round"
                onMouseEnter={() => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
              />
            );
          })}
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          <p className="text-4xl font-semibold tracking-tight text-ink tabular-nums">
            {formatNumber(activeIndex === null ? total : segments[activeIndex].value)}
          </p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.22em] text-ink-soft">
            {activeIndex === null ? totalLabel : segments[activeIndex].label}
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {segments.map((segment, index) => {
          const share = (segment.value / total) * 100;

          return (
            <button
              key={segment.label}
              type="button"
              onMouseEnter={() => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(null)}
              className={cn(
                "flex w-full items-center justify-between rounded-2xl border border-line/80 bg-muted/50 px-4 py-3 text-left transition-colors",
                activeIndex === index && "border-navy/20 bg-card"
              )}
            >
              <div className="flex items-center gap-3">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: colorMap[segment.color] }}
                />
                <span className="text-sm font-medium text-ink">{segment.label}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-ink tabular-nums">
                  {formatNumber(segment.value)}
                </p>
                <p className="text-xs text-ink-soft">{formatPercent(share)}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
