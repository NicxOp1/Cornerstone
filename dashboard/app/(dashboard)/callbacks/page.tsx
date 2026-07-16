import { CallbacksExplorer } from "@/components/CallbacksExplorer";
import { getCachedCallbacks } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

export default async function CallbacksPage() {
  const [emergencyCallbacks, generalCallbacks] = await Promise.all([
    getCachedCallbacks("emergency"),
    getCachedCallbacks("general")
  ]);

  return (
    <div className="space-y-6">
      <header className="rounded-[32px] border border-line/70 bg-card/80 p-6 shadow-panel md:p-8">
        <h1 className="font-display text-3xl tracking-tight text-ink md:text-5xl">Callbacks</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-soft">
          Every emergency and callback request Harmony logged — mark them off once the office follows up.
        </p>
      </header>

      <CallbacksExplorer emergencyCallbacks={emergencyCallbacks} generalCallbacks={generalCallbacks} />
    </div>
  );
}
