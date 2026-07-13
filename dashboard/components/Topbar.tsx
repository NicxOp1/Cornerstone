"use client";

import { formatSyncTimestamp, initialsFromUsername, presentUsername } from "@/lib/utils/format";

interface TopbarProps {
  onMenuClick: () => void;
  lastSyncedAt: string | null;
  username: string;
}

function SearchIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M15 17H5.5a1.5 1.5 0 0 1-1.2-2.4L6 12.5V10a6 6 0 1 1 12 0v2.5l1.7 2.1a1.5 1.5 0 0 1-1.2 2.4H15" />
      <path d="M10 19a2 2 0 0 0 4 0" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}

export function Topbar({ onMenuClick, lastSyncedAt, username }: TopbarProps) {
  const syncedLabel = formatSyncTimestamp(lastSyncedAt);
  const displayName = presentUsername(username);
  const initials = initialsFromUsername(username);

  return (
    <header className="sticky top-0 z-20 border-b border-line/70 bg-ground/85 backdrop-blur">
      <div className="flex min-h-[72px] items-center gap-3 px-4 md:px-6">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Toggle navigation"
          className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-line bg-card text-ink transition hover:border-navy/15 hover:text-navy"
        >
          <MenuIcon />
        </button>

        <label className="relative hidden max-w-xl flex-1 md:block">
          <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-ink-soft">
            <SearchIcon />
          </span>
          <input
            type="search"
            placeholder="Search calls, phone, summary"
            className="h-11 w-full rounded-full border border-line bg-card pl-11 pr-4 text-sm text-ink outline-none transition placeholder:text-ink-soft focus:border-navy/20"
          />
        </label>

        <div className="ml-auto flex items-center gap-3">
          {syncedLabel ? (
            <div className="hidden rounded-full border border-line bg-card px-4 py-2 text-xs font-medium text-ink-soft lg:block">
              Updated {syncedLabel}
            </div>
          ) : null}

          <button
            type="button"
            className="relative inline-flex h-11 w-11 items-center justify-center rounded-full border border-line bg-card text-ink transition hover:border-navy/15 hover:text-navy"
            aria-label="Notifications"
          >
            <BellIcon />
            <span className="absolute right-3 top-3 h-2.5 w-2.5 rounded-full bg-accent" />
          </button>

          <div className="flex items-center gap-3 rounded-full border border-line bg-card px-2 py-2 pl-2.5 pr-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-navy text-xs font-semibold uppercase tracking-[0.18em] text-white">
              {initials}
            </div>
            <div className="hidden md:block">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft">
                Signed in
              </p>
              <p className="text-sm font-semibold text-ink">{displayName}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
