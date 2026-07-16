"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

interface DashboardShellProps {
  children: React.ReactNode;
  lastSyncedAt: string | null;
  unreadCount: number;
  emergencyPendingCount: number;
  username: string;
}

const SIDEBAR_STORAGE_KEY = "dashboard-sidebar-collapsed";

export function DashboardShell({
  children,
  lastSyncedAt,
  unreadCount,
  emergencyPendingCount,
  username
}: DashboardShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    const savedState = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
    setSidebarCollapsed(savedState === "1");
  }, []);

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, sidebarCollapsed ? "1" : "0");
  }, [sidebarCollapsed]);

  function handleMenuClick() {
    if (window.innerWidth >= 768) {
      setSidebarCollapsed((current) => !current);
      return;
    }

    setSidebarOpen(true);
  }

  return (
    <div className="flex min-h-dvh bg-transparent">
      <Sidebar
        isOpen={sidebarOpen}
        isCollapsed={sidebarCollapsed}
        onClose={() => setSidebarOpen(false)}
        unreadCount={unreadCount}
        emergencyPendingCount={emergencyPendingCount}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={handleMenuClick} lastSyncedAt={lastSyncedAt} username={username} />
        <main className="flex-1 px-4 pb-6 pt-4 md:px-6 md:pb-8 md:pt-5 xl:px-7">{children}</main>
      </div>
    </div>
  );
}
