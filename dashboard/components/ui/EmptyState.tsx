import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";

interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <Card className="flex min-h-[220px] flex-col items-center justify-center overflow-hidden text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-[20px] border border-accent/20 bg-[#090d18] shadow-[0_18px_40px_rgba(0,0,0,0.24)]">
        <Logo variant="mark" className="h-10 w-10" />
      </div>
      <h3 className="mt-5 text-lg font-semibold text-ink">{title}</h3>
      <p className="mt-2 max-w-sm text-sm leading-6 text-ink-soft">{description}</p>
    </Card>
  );
}
