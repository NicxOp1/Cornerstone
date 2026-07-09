import { CallsTable } from "@/components/CallsTable";
import { getCachedCalls } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

interface LlamadasPageProps {
  searchParams: {
    sentiment?: string;
    serviceType?: string;
  };
}

export default async function LlamadasPage({ searchParams }: LlamadasPageProps) {
  const calls = await getCachedCalls({
    sentiment: searchParams.sentiment,
    serviceType: searchParams.serviceType
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Llamadas</h1>
      <CallsTable calls={calls} />
    </div>
  );
}
