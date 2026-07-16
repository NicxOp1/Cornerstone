import { revalidateTag } from "next/cache";
import { NextResponse } from "next/server";
import { CallbacksRepository } from "@/lib/data/callbacks-repository";
import { buildCallbacksWriteClient } from "@/lib/data/sheets-writer";
import type { CallbackKind } from "@/lib/types/callback";

function isValidKind(value: string): value is CallbackKind {
  return value === "emergency" || value === "general";
}

export async function PATCH(
  _request: Request,
  { params }: { params: { kind: string; callId: string } }
) {
  if (!isValidKind(params.kind)) {
    return NextResponse.json({ error: "kind must be 'emergency' or 'general'." }, { status: 400 });
  }

  const repository = new CallbacksRepository(buildCallbacksWriteClient());
  const ok = await repository.markReviewed(params.kind, params.callId);

  if (!ok) {
    return NextResponse.json({ error: "Callback no encontrado." }, { status: 404 });
  }

  revalidateTag("callbacks");
  return NextResponse.json({ status: "ok" });
}
