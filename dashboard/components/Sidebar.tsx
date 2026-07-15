"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils/cn";

const NAV_ITEMS = [
  { href: "/", icon: "overview", label: "Overview", matchers: ["/"] },
  { href: "/bookings", icon: "bookings", label: "Bookings", matchers: ["/bookings", "/reservas"] },
  {
    href: "/callbacks",
    icon: "callbacks",
    label: "Callbacks",
    matchers: ["/callbacks"]
  },
  {
    href: "/conversation",
    icon: "conversation",
    label: "Conversation",
    matchers: ["/conversation", "/conversacion"]
  },
  { href: "/cost", icon: "cost", label: "Cost", matchers: ["/cost", "/costo"] },
  { href: "/calls", icon: "calls", label: "Calls", matchers: ["/calls", "/llamadas"] },
  { href: "/messages", icon: "messages", label: "Messages", matchers: ["/messages", "/mensajes"] }
];

interface SidebarProps {
  isOpen: boolean;
  isCollapsed: boolean;
  onClose: () => void;
  unreadCount?: number;
  emergencyPendingCount?: number;
}

function isActivePath(pathname: string, matchers: string[]) {
  return matchers.some((matcher) => {
    if (matcher === "/") {
      return pathname === "/";
    }

    return pathname === matcher || pathname.startsWith(`${matcher}/`);
  });
}

function NavIcon({ icon }: { icon: string }) {
  switch (icon) {
    case "bookings":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M7 3v4M17 3v4M4 9h16M6 5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
        </svg>
      );
    case "conversation":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M6 17 3 21V6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6Z" />
          <path d="M8 9h8M8 13h5" />
        </svg>
      );
    case "cost":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 3v18M16 7.5c0-1.7-1.8-3-4-3s-4 1.3-4 3 1.1 2.5 4 3 4 1.3 4 3-1.8 3-4 3-4-1.3-4-3" />
        </svg>
      );
    case "calls":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M6.5 4h2.7L11 8.8l-1.8 1.8a14.6 14.6 0 0 0 4.2 4.2l1.8-1.8L20 14.8v2.7A2.5 2.5 0 0 1 17.5 20C9.5 20 3 13.5 3 5.5A2.5 2.5 0 0 1 5.5 3Z" />
        </svg>
      );
    case "messages":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M4 5h16v10H8l-4 4V5Z" />
        </svg>
      );
    case "callbacks":
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 9v4l2.5 2.5M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9Z" />
        </svg>
      );
    case "overview":
    default:
      return (
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M4 12h4v8H4zM10 8h4v12h-4zM16 4h4v16h-4z" />
        </svg>
      );
  }
}

export function Sidebar({ isOpen, isCollapsed, onClose, unreadCount = 0, emergencyPendingCount = 0 }: SidebarProps) {
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
        aria-label="Primary navigation"
        className={cn(
          "fixed inset-y-3 left-3 z-40 flex w-[280px] transform flex-col rounded-[32px] border border-white/10 bg-navy px-3 py-4 text-white shadow-[0_28px_90px_rgba(15,23,42,0.34)] transition-all duration-300 md:sticky md:top-3 md:h-[calc(100dvh-1.5rem)]",
          isOpen ? "translate-x-0" : "-translate-x-[calc(100%+1rem)] md:translate-x-0",
          isCollapsed ? "md:w-[88px]" : "md:w-[246px]"
        )}
      >
        <Link
          href="/"
          onClick={onClose}
          className="mb-6 flex items-center gap-3 rounded-[24px] bg-white/6 px-3 py-3"
          aria-label="Harmony overview"
        >
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-accent text-sm font-semibold uppercase tracking-[0.2em] text-accent-ink">
            H
          </div>
          <div className={cn("min-w-0", isCollapsed && "hidden")}>
            <p className="truncate text-sm font-semibold uppercase tracking-[0.2em] text-white/68">
              Harmony
            </p>
            <p className="truncate text-base font-semibold text-white">Cornerstone Services</p>
          </div>
        </Link>

        <ul className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const active = isActivePath(pathname, item.matchers);

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={onClose}
                  className={cn(
                    "group relative flex items-center rounded-[22px] px-3 py-3 text-sm font-medium transition-colors",
                    active ? "bg-white text-navy shadow-sm" : "text-white/72 hover:bg-white/8 hover:text-white"
                  )}
                >
                  <span
                    className={cn(
                      "absolute bottom-2 left-0 top-2 w-1 rounded-full bg-accent transition-opacity",
                      active ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/8 text-current group-hover:bg-white/12">
                    <NavIcon icon={item.icon} />
                  </span>
                  <span className={cn("ml-3 truncate", isCollapsed && "hidden")}>{item.label}</span>
                  {item.href === "/messages" && unreadCount > 0 ? (
                    <span
                      className={cn(
                        "ml-auto rounded-full bg-accent px-2 py-0.5 text-[11px] font-bold text-accent-ink",
                        isCollapsed && "absolute right-3 top-3 h-3 w-3 px-0 py-0 text-[0]"
                      )}
                    >
                      {isCollapsed ? "." : unreadCount}
                    </span>
                  ) : null}
                  {item.href === "/callbacks" && emergencyPendingCount > 0 ? (
                    <span
                      className={cn(
                        "ml-auto rounded-full bg-bad px-2 py-0.5 text-[11px] font-bold text-white",
                        isCollapsed && "absolute right-3 top-3 h-3 w-3 px-0 py-0 text-[0]"
                      )}
                    >
                      {isCollapsed ? "." : emergencyPendingCount}
                    </span>
                  ) : null}
                </Link>
              </li>
            );
          })}
        </ul>

        <div
          className={cn(
            "mt-auto rounded-[24px] border border-white/10 bg-white/6 px-3 py-4",
            isCollapsed && "hidden"
          )}
        >
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/55">
            Shared access
          </p>
          <p className="mt-2 text-sm leading-6 text-white/76">
            Calls and messages stay under one shared login until role-based access is needed.
          </p>
        </div>
      </nav>
    </>
  );
}
