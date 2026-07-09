import { Logo } from "@/components/Logo";
import { LoginForm } from "@/components/LoginForm";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  return (
    <main className="min-h-dvh px-4 py-10 md:px-6">
      <div className="mx-auto grid w-full max-w-6xl gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <section className="relative overflow-hidden rounded-[38px] border border-line/70 bg-[linear-gradient(180deg,rgba(10,13,25,0.96),rgba(18,24,43,0.94))] p-8 shadow-panel md:p-10 lg:min-h-[580px]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(245,224,0,0.22),transparent_34%),radial-gradient(circle_at_bottom_left,rgba(81,92,191,0.24),transparent_30%)]" />
          <div className="relative flex h-full flex-col justify-between gap-10">
            <div className="space-y-6">
              <span className="inline-flex items-center rounded-full border border-accent/20 bg-accent/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
                Cornerstone voice ops
              </span>
              <Logo className="h-16 md:h-20" />
              <div className="max-w-2xl">
                <h1 className="font-display text-4xl leading-none tracking-tight text-white md:text-6xl">
                  Harmony dashboard, brought into the brand.
                </h1>
                <p className="mt-5 max-w-xl text-base leading-7 text-white/70">
                  Review bookings, conversation quality, calls, and spend from one brighter command
                  center built around Cornerstone&apos;s visual identity.
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/55">Bookings</p>
                <p className="mt-3 text-lg font-semibold text-white">Funnel visibility</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/55">Conversation</p>
                <p className="mt-3 text-lg font-semibold text-white">Sentiment + quality</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/55">Cost</p>
                <p className="mt-3 text-lg font-semibold text-white">Daily spend tracking</p>
              </div>
            </div>
          </div>
        </section>

        <div className="rounded-[34px] border border-line/70 bg-card/92 p-8 shadow-panel md:p-10">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-[22px] border border-accent/18 bg-[#080c16]">
              <Logo variant="mark" className="h-10 w-10" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent/80">Harmony</p>
              <h1 className="text-2xl font-semibold tracking-tight text-ink">Cornerstone dashboard</h1>
            </div>
          </div>
          <p className="mt-6 text-sm leading-6 text-ink-soft">
            Shared access for the team. Sign in to review calls, bookings, and feedback.
          </p>
          <LoginForm />
        </div>
      </div>
    </main>
  );
}
