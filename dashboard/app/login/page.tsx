import { LoginForm } from "@/components/LoginForm";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh items-center justify-center px-4">
      <div className="w-full max-w-md rounded-[32px] border border-line bg-card p-8 shadow-panel">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-accent text-lg font-semibold uppercase tracking-[0.24em] text-accent-ink">
            H
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-soft">
              Harmony
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-ink">Cornerstone dashboard</h1>
          </div>
        </div>
        <p className="mt-6 text-sm leading-6 text-ink-soft">
          Shared access for the team. Sign in to review calls, bookings, and feedback.
        </p>
        <LoginForm />
      </div>
    </main>
  );
}
