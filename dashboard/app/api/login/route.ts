import { NextRequest, NextResponse } from "next/server";
import { verifyPassword } from "@/lib/auth/password";
import { clearAttempts, isRateLimited, recordFailedAttempt } from "@/lib/auth/rate-limit";
import {
  createSessionToken,
  SESSION_COOKIE_NAME,
  SESSION_DURATION_SECONDS
} from "@/lib/auth/session";

interface DashboardCredential {
  passwordHash: string;
  username: string;
}

function isLoginRateLimitEnabled(): boolean {
  return process.env.DISABLE_LOGIN_RATE_LIMIT !== "true";
}

function getRequestIp(request: NextRequest): string {
  const header = request.headers.get("x-forwarded-for") ?? "";
  const ip = header.split(",")[0]?.trim();
  return ip || "unknown";
}

function getConfiguredCredentials(): DashboardCredential[] {
  return [
    {
      username: process.env.DASHBOARD_USERNAME ?? "",
      passwordHash: process.env.DASHBOARD_PASSWORD ?? ""
    },
    {
      username: process.env.DASHBOARD_SECONDARY_USERNAME ?? "",
      passwordHash: process.env.DASHBOARD_SECONDARY_PASSWORD ?? ""
    }
  ].filter(
    (credential): credential is DashboardCredential =>
      credential.username.trim() !== "" && credential.passwordHash.trim() !== ""
  );
}

export async function POST(request: NextRequest) {
  const ip = getRequestIp(request);
  const rateLimitEnabled = isLoginRateLimitEnabled();

  if (rateLimitEnabled && isRateLimited(ip)) {
    return NextResponse.json(
      { error: "Demasiados intentos. Proba de nuevo en unos minutos." },
      { status: 429 }
    );
  }

  const body = await request.json().catch(() => ({}));
  const { username, password } = body as { username?: string; password?: string };
  const credentials = getConfiguredCredentials();
  const matchedCredential = credentials.find((credential) => credential.username === username);
  const passwordMatches = matchedCredential
    ? await verifyPassword(password ?? "", matchedCredential.passwordHash)
    : false;

  if (!matchedCredential || !passwordMatches) {
    if (rateLimitEnabled) {
      recordFailedAttempt(ip);
    }
    return NextResponse.json({ error: "Usuario o contrasena incorrectos." }, { status: 401 });
  }

  if (rateLimitEnabled) {
    clearAttempts(ip);
  }

  const token = await createSessionToken(matchedCredential.username);
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
