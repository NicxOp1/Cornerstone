import { DashboardShell } from "@/components/DashboardShell";
import { getCachedUnreadCount } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const unreadCount = await getCachedUnreadCount();

  return <DashboardShell unreadCount={unreadCount}>{children}</DashboardShell>;
}
