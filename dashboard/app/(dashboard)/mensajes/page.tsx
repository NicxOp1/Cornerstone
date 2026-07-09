import { MessageComposer } from "@/components/MessageComposer";
import { cn } from "@/lib/utils/cn";
import { getCachedMessages } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

export default async function MensajesPage() {
  const messages = await getCachedMessages();

  return (
    <div className="flex h-[calc(100dvh-3.5rem)] flex-col">
      <h1 className="p-4 text-xl font-bold">Mensajes</h1>
      <div className="flex-1 space-y-2 overflow-y-auto px-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "max-w-[80%] rounded-2xl px-4 py-2 text-sm",
              message.sender === "john"
                ? "mr-auto bg-gray-100 dark:bg-white/10"
                : "ml-auto bg-cornerstone-navy text-cornerstone-yellow"
            )}
          >
            <p>{message.text}</p>
            <p className="mt-1 text-[10px] opacity-60">
              {message.sender === "john" ? "John" : "Equipo"}
            </p>
          </div>
        ))}
        {messages.length === 0 ? (
          <p className="text-center text-sm text-gray-400">Todavia no hay mensajes.</p>
        ) : null}
      </div>
      <MessageComposer defaultSender="john" />
    </div>
  );
}
