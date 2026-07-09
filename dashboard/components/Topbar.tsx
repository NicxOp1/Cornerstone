"use client";

interface TopbarProps {
  onMenuClick: () => void;
  lastSyncedAt: string | null;
}

export function Topbar({ onMenuClick, lastSyncedAt }: TopbarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-white/10 dark:bg-gray-950">
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Abrir menu"
        className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-white/10 md:hidden"
      >
        Menu
      </button>
      <span className="font-bold text-cornerstone-navy dark:text-white">Cornerstone</span>
      <span className="text-xs text-gray-500 dark:text-gray-400">
        {lastSyncedAt ? `Ultima actualizacion: ${lastSyncedAt}` : ""}
      </span>
    </header>
  );
}
