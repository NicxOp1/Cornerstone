import { cn } from "@/lib/utils/cn";

interface TooltipRow {
  label: string;
  value: string;
}

interface ChartTooltipProps {
  title: string;
  rows: TooltipRow[];
  x: number;
  y: number;
  visible: boolean;
}

export function ChartTooltip({ title, rows, x, y, visible }: ChartTooltipProps) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute z-20 min-w-[190px] rounded-[20px] border border-accent/20 bg-[#070c18]/96 px-4 py-3 text-sm text-white shadow-[0_24px_60px_rgba(0,0,0,0.48)] backdrop-blur-md transition-opacity",
        visible ? "opacity-100" : "opacity-0"
      )}
      style={{
        left: x,
        top: y,
        transform: "translate(-50%, calc(-100% - 14px))"
      }}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent/80">{title}</p>
      <div className="mt-3 space-y-2">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between gap-6">
            <span className="text-white/68">{row.label}</span>
            <span className="font-semibold tabular-nums text-white">{row.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
