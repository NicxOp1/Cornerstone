interface AttemptRecord {
  count: number;
  windowStartedAt: number;
}

const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000;

const attempts = new Map<string, AttemptRecord>();

export function isRateLimited(key: string): boolean {
  const record = attempts.get(key);

  if (!record) {
    return false;
  }

  if (Date.now() - record.windowStartedAt > WINDOW_MS) {
    attempts.delete(key);
    return false;
  }

  return record.count >= MAX_ATTEMPTS;
}

export function recordFailedAttempt(key: string): void {
  const record = attempts.get(key);

  if (!record || Date.now() - record.windowStartedAt > WINDOW_MS) {
    attempts.set(key, { count: 1, windowStartedAt: Date.now() });
    return;
  }

  record.count += 1;
}

export function clearAttempts(key: string): void {
  attempts.delete(key);
}
