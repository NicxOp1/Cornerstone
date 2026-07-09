import { cn } from "@/lib/utils/cn";

export type ChipTone = "bad" | "good" | "neg" | "neu" | "neutral" | "pos" | "warn";

const toneClasses: Record<ChipTone, string> = {
  good: "bg-good-soft text-good",
  bad: "bg-bad-soft text-bad",
  warn: "bg-accent/20 text-ink",
  neutral: "bg-muted text-ink-soft",
  pos: "bg-good-soft text-good",
  neu: "bg-muted text-ink-soft",
  neg: "bg-bad-soft text-bad"
};

export function StatusChip({ tone, label }: { tone: ChipTone; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
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
