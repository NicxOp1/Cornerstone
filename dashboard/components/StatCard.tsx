import { Card } from "@/components/ui/Card";

interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string;
}

export function StatCard({ label, value, sublabel }: StatCardProps) {
  return (
    <Card className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft">{label}</p>
      <p className="text-2xl font-semibold tracking-tight text-ink tabular-nums">{value}</p>
      {sublabel ? <p className="text-xs text-ink-soft">{sublabel}</p> : null}
    </Card>
  );
}
