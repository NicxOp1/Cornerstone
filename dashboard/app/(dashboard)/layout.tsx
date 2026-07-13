import { DashboardShell } from "@/components/DashboardShell";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/auth/session";
import { getCachedSummaryMetrics, getCachedUnreadCount } from "@/lib/data/cached-repository";
import { cookies } from "next/headers";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const token = cookies().get(SESSION_COOKIE_NAME)?.value ?? "";
  const [unreadCount, summary, session] = await Promise.all([
    getCachedUnreadCount(),
    getCachedSummaryMetrics(),
    verifySessionToken(token)
  ]);

  return (
    <DashboardShell
      unreadCount={unreadCount}
      lastSyncedAt={summary.lastSyncedAt}
      username={session?.username ?? "team"}
    >
      {children}
    </DashboardShell>
  );
}
