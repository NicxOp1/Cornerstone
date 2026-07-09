"use client";

import { Logo } from "@/components/Logo";

interface TopbarProps {
  onMenuClick: () => void;
  lastSyncedAt: string | null;
}

export function Topbar({ onMenuClick, lastSyncedAt }: TopbarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-white/10 dark:bg-gray-950">
      {/* Izquierda: en mobile, boton de menu + logo (el sidebar esta oculto como drawer).
          En desktop el logo vive en el sidebar, asi que aca queda vacio. */}
      <div className="flex items-center gap-2 md:hidden">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Abrir menu"
          className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-white/10"
        >
          Menu
        </button>
        <Logo tone="onLight" className="h-7" />
      </div>
      <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">
        {lastSyncedAt ? `Ultima actualizacion: ${lastSyncedAt}` : ""}
      </span>
    </header>
  );
}
