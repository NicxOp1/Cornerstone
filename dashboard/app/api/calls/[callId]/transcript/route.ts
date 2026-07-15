import { NextResponse } from "next/server";
import { extractTranscriptTurns, fetchRetellCall, RetellCallError } from "@/lib/retell-call";

export async function GET(
  _request: Request,
  { params }: { params: { callId: string } }
) {
  try {
    const call = await fetchRetellCall(params.callId);
    return NextResponse.json(extractTranscriptTurns(call), {
      headers: {
        "Cache-Control": "no-store"
      }
    });
  } catch (error) {
    if (error instanceof RetellCallError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }

    return NextResponse.json({ error: "Unexpected error loading transcript." }, { status: 500 });
  }
}
