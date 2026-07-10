import { NextResponse } from "next/server";
import { fetchRetellCall, pickRecordingUrl, RetellCallError } from "@/lib/retell-call";

export async function GET(
  _request: Request,
  { params }: { params: { callId: string } }
) {
  try {
    const call = await fetchRetellCall(params.callId);
    const recordingUrl = pickRecordingUrl(call);

    if (!recordingUrl) {
      return NextResponse.json({ error: "Recording unavailable for this call." }, { status: 404 });
    }

    return NextResponse.redirect(recordingUrl, {
      status: 307,
      headers: {
        "Cache-Control": "no-store"
      }
    });
  } catch (error) {
    if (error instanceof RetellCallError) {
      return NextResponse.json({ error: error.message }, { status: error.status });
    }

    return NextResponse.json({ error: "Unexpected error loading recording." }, { status: 500 });
  }
}
