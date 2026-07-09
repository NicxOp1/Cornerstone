import { revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";
import { MessagesRepository } from "@/lib/data/messages-repository";
import { buildWriteClient } from "@/lib/data/sheets-writer";
import type { MessageSender } from "@/lib/types/message";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const { text, sender } = body as { text?: string; sender?: MessageSender };

  if (!text || !sender) {
    return NextResponse.json({ error: "text y sender son obligatorios." }, { status: 400 });
  }

  const repository = new MessagesRepository(buildWriteClient());
  const entry = await repository.addMessage(sender, text);

  revalidateTag("messages");
  return NextResponse.json(entry, { status: 201 });
}
