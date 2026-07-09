import { revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";
import { FeedbackRepository } from "@/lib/data/feedback-repository";
import { buildWriteClient } from "@/lib/data/sheets-writer";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const { callId, comment } = body as { callId?: string; comment?: string };

  if (!callId || !comment) {
    return NextResponse.json({ error: "callId y comment son obligatorios." }, { status: 400 });
  }

  const repository = new FeedbackRepository(buildWriteClient());
  const entry = await repository.addFeedback(callId, comment);

  revalidateTag("feedback");
  return NextResponse.json(entry, { status: 201 });
}
