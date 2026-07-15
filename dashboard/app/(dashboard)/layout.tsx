import { DashboardShell } from "@/components/DashboardShell";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/auth/session";
import {
  getCachedEmergencyPendingCount,
  getCachedSummaryMetrics,
  getCachedUnreadCount
} from "@/lib/data/cached-repository";
import { cookies } from "next/headers";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const token = cookies().get(SESSION_COOKIE_NAME)?.value ?? "";
  const [unreadCount, emergencyPendingCount, summary, session] = await Promise.all([
    getCachedUnreadCount(),
    getCachedEmergencyPendingCount(),
    getCachedSummaryMetrics(),
    verifySessionToken(token)
  ]);

  return (
    <DashboardShell
      unreadCount={unreadCount}
      emergencyPendingCount={emergencyPendingCount}
      lastSyncedAt={summary.lastSyncedAt}
      username={session?.username ?? "team"}
    >
      {children}
    </DashboardShell>
  );
}
