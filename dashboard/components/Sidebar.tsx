"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
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
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={onClose}
                className={cn(
                  "block rounded-lg px-3 py-2 text-sm font-medium hover:bg-white/10",
                  pathname === item.href &&
                    "bg-cornerstone-yellow text-cornerstone-navy hover:bg-cornerstone-yellow"
                )}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
