const monthDayFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC"
});

const syncFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit"
});

export function parseDay(day: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(day);

  if (!match) {
    return null;
  }

  return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
}

export function addUtcDays(date: Date, days: number): Date {
  const next = new Date(date.getTime());
  next.setUTCDate(next.getUTCDate() + days);
  return next;
}

export function toDayKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function inclusiveDaySpan(start: Date, end: Date): number {
  return Math.max(1, Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1);
}

export function formatDayShort(day: string): string {
  const parsed = parseDay(day);
  return parsed ? monthDayFormatter.format(parsed) : day;
}

export function formatRangeEyebrow(startDay: string, endDay: string): string {
  const start = parseDay(startDay);
  const end = parseDay(endDay);

  if (!start || !end) {
    return "";
  }

  const span = inclusiveDaySpan(start, end);
  const startLabel = monthDayFormatter.format(start).toUpperCase();
  const endLabel = monthDayFormatter.format(end).toUpperCase();

  return `LAST ${span} DAYS / ${startLabel} - ${endLabel}`;
}

export function formatDuration(seconds: number): string {
  const safeSeconds = Number.isFinite(seconds) ? Math.max(0, Math.round(seconds)) : 0;
  const minutes = Math.floor(safeSeconds / 60);
  const remaining = safeSeconds % 60;
  return `${minutes}:${String(remaining).padStart(2, "0")}`;
}

export function formatPercent(value: number): string {
  return `${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: value % 1 === 0 ? 0 : 1,
    maximumFractionDigits: 1
  }).format(value)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatCurrency(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(cents / 100);
}

export function formatCompactCost(cents: number): string {
  const absolute = Math.abs(cents);

  if (absolute < 100) {
    return `${new Intl.NumberFormat("en-US", {
      maximumFractionDigits: absolute % 1 === 0 ? 0 : 1
    }).format(cents)}c`;
  }

  return formatCurrency(cents);
}

export function formatSyncTimestamp(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : syncFormatter.format(parsed);
}

export function presentUsername(username: string): string {
  const parts = username
    .split(/[\s._-]+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return "Team";
  }

  return parts
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function initialsFromUsername(username: string): string {
  const parts = username
    .split(/[\s._-]+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return "HM";
  }

  return parts
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}
