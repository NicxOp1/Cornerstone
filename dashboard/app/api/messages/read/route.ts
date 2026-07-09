import { revalidateTag } from "next/cache";
import { NextResponse } from "next/server";
import { MessagesRepository } from "@/lib/data/messages-repository";
import { buildWriteClient } from "@/lib/data/sheets-writer";

export async function POST() {
  const repository = new MessagesRepository(buildWriteClient());
  await repository.markAllReadByEquipo();

  revalidateTag("messages");
  return NextResponse.json({ status: "ok" });
}
