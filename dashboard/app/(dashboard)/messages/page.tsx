import { MessageComposer } from "@/components/MessageComposer";
import { cn } from "@/lib/utils/cn";
import { getCachedMessages } from "@/lib/data/cached-repository";

export const dynamic = "force-dynamic";

export default async function MessagesPage() {
  const messages = await getCachedMessages();

  return (
    <div className="flex h-[calc(100dvh-2rem)] flex-col overflow-hidden rounded-[32px] border border-line/70 bg-card/80 shadow-panel">
      <header className="border-b border-line/70 px-6 py-5">
        <h1 className="font-display text-2xl tracking-tight text-ink">Messages</h1>
        <p className="mt-1 text-sm text-ink-soft">A direct line with John — one continuous thread.</p>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-6 py-5">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "max-w-[78%] rounded-[20px] px-4 py-2.5 text-sm shadow-sm",
              message.sender === "john"
                ? "mr-auto rounded-tl-sm bg-muted/70 text-ink"
                : "ml-auto rounded-tr-sm bg-navy text-white"
            )}
          >
            <p>{message.text}</p>
            <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.14em] opacity-60">
              {message.sender === "john" ? "John" : "Team"}
            </p>
          </div>
        ))}
        {messages.length === 0 ? (
          <p className="pt-10 text-center text-sm text-ink-soft">No messages yet. Start the conversation below.</p>
        ) : null}
      </div>

      <MessageComposer defaultSender="john" />
    </div>
  );
}
