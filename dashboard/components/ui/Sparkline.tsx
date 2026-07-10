import { cn } from "@/lib/utils/cn";

const toneMap = {
  accent: "rgb(var(--accent))",
  bad: "rgb(var(--bad))",
  good: "rgb(var(--good))",
  ink: "rgb(var(--heat))"
} as const;

interface SparklineProps {
  points: number[];
  tone?: keyof typeof toneMap;
  className?: string;
}

// Padding vertical (en unidades de viewBox) para que la línea no toque los bordes.
const PAD_Y = 16;

export function Sparkline({ points, tone = "accent", className }: SparklineProps) {
  const safePoints = points.length > 0 ? points : [0];
  const min = Math.min(...safePoints);
  const max = Math.max(...safePoints);
  const range = max - min || 1;
  const color = toneMap[tone];
  const gradientId = `spark-${tone}`;

  const coords = safePoints.map((point, index) => {
    const x = safePoints.length === 1 ? 50 : (index / (safePoints.length - 1)) * 100;
    const y = PAD_Y + (1 - (point - min) / range) * (100 - PAD_Y * 2);
    return { x, y };
  });

  const linePath = coords.map(({ x, y }, index) => `${index === 0 ? "M" : "L"}${x} ${y}`).join(" ");
  const areaPath = `${linePath} L100 100 L0 100 Z`;

  return (
    <svg
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      aria-hidden="true"
      className={cn("h-full w-full overflow-visible", className)}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${gradientId})`} stroke="none" />
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
