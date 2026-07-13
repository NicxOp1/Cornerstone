import { formatNumber, formatPercent } from "@/lib/utils/format";

export interface FunnelStage {
  label: string;
  value: number;
  hint?: string;
}

export function FunnelBars({ stages }: { stages: FunnelStage[] }) {
  const max = Math.max(...stages.map((stage) => stage.value), 1);
  const first = stages[0]?.value || 1;

  return (
    <div className="space-y-4">
      {stages.map((stage, index) => {
        const width = Math.max(5, (stage.value / max) * 100);
        const share = (stage.value / first) * 100;
        const isLast = index === stages.length - 1;

        return (
          <div key={stage.label} className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="font-medium text-ink">{stage.label}</span>
              <span className="tabular-nums text-ink-soft">
                {formatNumber(stage.value)}
                <span className="ml-2 text-ink-soft/70">{formatPercent(share)}</span>
              </span>
            </div>
            <div className="h-10 w-full overflow-hidden rounded-2xl bg-muted/60">
              <div
                className="flex h-full items-center rounded-2xl px-3 text-xs font-semibold text-white transition-all"
                style={{
                  width: `${width}%`,
                  backgroundColor: isLast ? "rgb(var(--accent))" : "rgb(var(--navy))",
                  color: isLast ? "rgb(var(--accent-ink))" : "#fff"
                }}
              >
                {stage.hint ? <span className="truncate">{stage.hint}</span> : null}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
