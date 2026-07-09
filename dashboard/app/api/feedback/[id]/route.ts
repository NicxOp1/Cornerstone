import { revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";
import { FeedbackRepository } from "@/lib/data/feedback-repository";
import { buildWriteClient } from "@/lib/data/sheets-writer";

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await request.json().catch(() => ({}));
  const { reply } = body as { reply?: string };

  if (!reply) {
    return NextResponse.json({ error: "reply es obligatorio." }, { status: 400 });
  }

  const repository = new FeedbackRepository(buildWriteClient());
  const updated = await repository.addReply(params.id, reply);

  if (!updated) {
    return NextResponse.json({ error: "Feedback no encontrado." }, { status: 404 });
  }

  revalidateTag("feedback");
  return NextResponse.json({ status: "ok" });
}
