import { jwtVerify, SignJWT } from "jose";

export const SESSION_COOKIE_NAME = "dashboard_session";
export const SESSION_DURATION_SECONDS = 30 * 24 * 60 * 60;

function getSecretKey(): Uint8Array {
  const secret = process.env.SESSION_SECRET;

  if (!secret) {
    throw new Error("SESSION_SECRET no configurado");
  }

  return new TextEncoder().encode(secret);
}

export async function createSessionToken(username: string): Promise<string> {
  return new SignJWT({ username })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_DURATION_SECONDS}s`)
    .sign(getSecretKey());
}

export async function verifySessionToken(token: string): Promise<{ username: string } | null> {
  if (!token) {
    return null;
  }

  try {
    const { payload } = await jwtVerify(token, getSecretKey());

    if (typeof payload.username !== "string") {
      return null;
    }

    return { username: payload.username };
  } catch {
    return null;
  }
}
