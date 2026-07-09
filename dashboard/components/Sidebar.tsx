"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";
import { cn } from "@/lib/utils/cn";

const NAV_ITEMS = [
  { href: "/", label: "Resumen" },
  { href: "/volumen", label: "Volumen" },
  { href: "/reservas", label: "Reservas" },
  { href: "/conversacion", label: "Conversacion" },
  { href: "/costo", label: "Costo" },
  { href: "/llamadas", label: "Llamadas" },
  { href: "/mensajes", label: "Mensajes" }
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  unreadCount?: number;
}

export function Sidebar({ isOpen, onClose, unreadCount = 0 }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {isOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      ) : null}
      <nav
        aria-label="Navegacion principal"
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 transform bg-cornerstone-navy p-4 text-white transition-transform duration-200 md:static md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Link href="/" onClick={onClose} className="mb-6 block px-2" aria-label="Cornerstone - Inicio">
          <Logo tone="onDark" className="h-10" />
        </Link>
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium hover:bg-white/10",
                  pathname === item.href &&
                    "bg-cornerstone-yellow text-cornerstone-navy hover:bg-cornerstone-yellow"
                )}
              >
                <span>{item.label}</span>
                {item.href === "/mensajes" && unreadCount > 0 ? (
                  <span className="ml-2 rounded-full bg-cornerstone-yellow px-2 py-0.5 text-xs font-bold text-cornerstone-navy">
                    {unreadCount}
                  </span>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
