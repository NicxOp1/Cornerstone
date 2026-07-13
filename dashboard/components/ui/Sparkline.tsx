import { cn } from "@/lib/utils/cn";

const toneClasses = {
  accent: "stroke-accent",
  bad: "stroke-bad",
  good: "stroke-good",
  ink: "stroke-ink"
} as const;

interface SparklineProps {
  points: number[];
  tone?: keyof typeof toneClasses;
  className?: string;
}

export function Sparkline({ points, tone = "accent", className }: SparklineProps) {
  const safePoints = points.length > 0 ? points : [0];
  const min = Math.min(...safePoints);
  const max = Math.max(...safePoints);
  const range = max - min || 1;

  const polylinePoints = safePoints
    .map((point, index) => {
      const x = safePoints.length === 1 ? 50 : (index / (safePoints.length - 1)) * 100;
      const y = 100 - ((point - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 100 100" aria-hidden="true" className={cn("h-full w-full", className)}>
      <polyline
        points={polylinePoints}
        fill="none"
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={cn("fill-none", toneClasses[tone])}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
