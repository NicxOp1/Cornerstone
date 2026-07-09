interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string;
}

export function StatCard({ label, value, sublabel }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-gray-900">
      <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-cornerstone-navy dark:text-white">{value}</p>
      {sublabel ? <p className="mt-1 text-xs text-gray-400">{sublabel}</p> : null}
    </div>
  );
}
