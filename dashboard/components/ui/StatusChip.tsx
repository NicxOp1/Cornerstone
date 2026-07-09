import { cn } from "@/lib/utils/cn";

export type ChipTone = "bad" | "good" | "neg" | "neu" | "neutral" | "pos" | "warn";

const toneClasses: Record<ChipTone, string> = {
  good: "border border-good/20 bg-good-soft/90 text-good",
  bad: "border border-bad/20 bg-bad-soft/90 text-bad",
  warn: "border border-accent/18 bg-accent/16 text-accent",
  neutral: "border border-white/6 bg-muted/90 text-ink-soft",
  pos: "border border-good/20 bg-good-soft/90 text-good",
  neu: "border border-line/80 bg-muted/90 text-[rgb(var(--heat))]",
  neg: "border border-bad/20 bg-bad-soft/90 text-bad"
};

export function StatusChip({ tone, label }: { tone: ChipTone; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
        toneClasses[tone]
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {label}
    </span>
  );
}

export function sentimentTone(sentiment: string): ChipTone {
  const value = sentiment.trim().toLowerCase();
  if (value === "positive") return "pos";
  if (value === "negative") return "neg";
  if (value === "neutral") return "neu";
  return "neutral";
}

export function bookingTone(status: string): ChipTone {
  switch (status) {
    case "confirmed":
      return "good";
    case "pending":
      return "warn";
    case "mismatch":
      return "bad";
    default:
      return "neutral";
  }
}

export function bookingLabel(status: string): string {
  switch (status) {
    case "confirmed":
      return "Confirmed";
    case "pending":
      return "Pending";
    case "mismatch":
      return "Mismatch";
    default:
      return "No booking";
  }
}
