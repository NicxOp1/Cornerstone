import Link from "next/link";
import type { Call } from "@/lib/types/call";

interface CallsTableProps {
  calls: Call[];
}

export function CallsTable({ calls }: CallsTableProps) {
  if (calls.length === 0) {
    return (
      <p className="rounded-2xl border border-gray-200 bg-white p-6 text-center text-sm text-gray-400 dark:border-white/10 dark:bg-gray-900">
        No hay llamadas que coincidan con estos filtros.
      </p>
    );
  }

  return (
    <>
      <ul className="space-y-2 md:hidden">
        {calls.map((call) => (
          <li key={call.callId}>
            <Link
              href={`/llamadas/${call.callId}`}
              className="block rounded-2xl border border-gray-200 bg-white p-4 dark:border-white/10 dark:bg-gray-900"
            >
              <div className="flex justify-between text-sm font-medium">
                <span>{call.fromNumber || "Numero desconocido"}</span>
                <span>{call.callSuccessful ? "OK" : "NO"}</span>
              </div>
              <p className="text-xs text-gray-500">
                {call.day} {call.startTime} · {call.durationS}s
              </p>
              <p className="text-xs text-gray-500">
                {call.serviceType} · {call.sentiment}
              </p>
            </Link>
          </li>
        ))}
      </ul>

      <table className="hidden w-full overflow-hidden rounded-2xl border border-gray-200 bg-white text-sm dark:border-white/10 dark:bg-gray-900 md:table">
        <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-white/5">
          <tr>
            <th className="px-4 py-2">Fecha</th>
            <th className="px-4 py-2">Telefono</th>
            <th className="px-4 py-2">Duracion</th>
            <th className="px-4 py-2">Servicio</th>
            <th className="px-4 py-2">Sentimiento</th>
            <th className="px-4 py-2">Exito</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-white/10">
          {calls.map((call) => (
            <tr key={call.callId} className="hover:bg-gray-50 dark:hover:bg-white/5">
              <td className="px-4 py-2">
                <Link href={`/llamadas/${call.callId}`} className="block">
                  {call.day} {call.startTime}
                </Link>
              </td>
              <td className="px-4 py-2">{call.fromNumber || "-"}</td>
              <td className="px-4 py-2">{call.durationS}s</td>
              <td className="px-4 py-2">{call.serviceType || "-"}</td>
              <td className="px-4 py-2">{call.sentiment}</td>
              <td className="px-4 py-2">{call.callSuccessful ? "OK" : "NO"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
