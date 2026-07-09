import { NextRequest, NextResponse } from "next/server";
import { verifyPassword } from "@/lib/auth/password";
import { clearAttempts, isRateLimited, recordFailedAttempt } from "@/lib/auth/rate-limit";
import {
  createSessionToken,
  SESSION_COOKIE_NAME,
  SESSION_DURATION_SECONDS
} from "@/lib/auth/session";

function getRequestIp(request: NextRequest): string {
  const header = request.headers.get("x-forwarded-for") ?? "";
  const ip = header.split(",")[0]?.trim();
  return ip || "unknown";
}

export async function POST(request: NextRequest) {
  const ip = getRequestIp(request);

  if (isRateLimited(ip)) {
    return NextResponse.json(
      { error: "Demasiados intentos. Proba de nuevo en unos minutos." },
      { status: 429 }
    );
  }

  const body = await request.json().catch(() => ({}));
  const { username, password } = body as { username?: string; password?: string };

  const expectedUsername = process.env.DASHBOARD_USERNAME ?? "";
  const expectedPasswordHash = process.env.DASHBOARD_PASSWORD ?? "";

  const usernameMatches = expectedUsername !== "" && username === expectedUsername;
  const passwordMatches =
    usernameMatches && (await verifyPassword(password ?? "", expectedPasswordHash));

  if (!usernameMatches || !passwordMatches) {
    recordFailedAttempt(ip);
    return NextResponse.json({ error: "Usuario o contrasena incorrectos." }, { status: 401 });
  }

  clearAttempts(ip);

  const token = await createSessionToken(username as string);
  const response = NextResponse.json({ status: "ok" });

  response.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: SESSION_DURATION_SECONDS,
    path: "/"
  });

  return response;
}
