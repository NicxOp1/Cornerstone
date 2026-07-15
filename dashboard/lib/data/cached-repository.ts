import { unstable_cache } from "next/cache";
import type { CallFilters } from "@/lib/data/repository";
import { CallbacksRepository } from "@/lib/data/callbacks-repository";
import { FeedbackRepository } from "@/lib/data/feedback-repository";
import { MessagesRepository } from "@/lib/data/messages-repository";
import { buildProductionRepository } from "@/lib/data/sheets-repository";
import { buildCallbacksWriteClient, buildWriteClient } from "@/lib/data/sheets-writer";
import type { CallbackKind } from "@/lib/types/callback";

const repository = buildProductionRepository();
const writeClient = buildWriteClient();
const feedbackRepository = new FeedbackRepository(writeClient);
const messagesRepository = new MessagesRepository(writeClient);
const callbacksRepository = new CallbacksRepository(buildCallbacksWriteClient());

export function getCachedCalls(filters: CallFilters = {}) {
  return unstable_cache(() => repository.getCalls(filters), ["calls", JSON.stringify(filters)], {
    revalidate: 60,
    tags: ["calls"]
  })();
}

export function getCachedCallById(callId: string) {
  return unstable_cache(() => repository.getCallById(callId), ["calls", "byId", callId], {
    revalidate: 60,
    tags: ["calls"]
  })();
}

export function getCachedSummaryMetrics() {
  return unstable_cache(() => repository.getSummaryMetrics(), ["calls", "summary"], {
    revalidate: 60,
    tags: ["summary"]
  })();
}

export function getCachedFeedbackForCall(callId: string) {
  return unstable_cache(() => feedbackRepository.getFeedbackForCall(callId), ["feedback", callId], {
    revalidate: 60,
    tags: ["feedback"]
  })();
}

export function getCachedMessages() {
  return unstable_cache(() => messagesRepository.listMessages(), ["messages"], {
    revalidate: 60,
    tags: ["messages"]
  })();
}

export function getCachedUnreadCount() {
  return unstable_cache(() => messagesRepository.countUnreadForEquipo(), ["messages", "unread"], {
    revalidate: 60,
    tags: ["messages"]
  })();
}

export function getCachedCallbacks(kind: CallbackKind) {
  return unstable_cache(() => callbacksRepository.listCallbacks(kind), ["callbacks", kind], {
    revalidate: 60,
    tags: ["callbacks"]
  })();
}

export function getCachedEmergencyPendingCount() {
  return unstable_cache(
    () => callbacksRepository.countPending("emergency"),
    ["callbacks", "emergency", "pending-count"],
    {
      revalidate: 60,
      tags: ["callbacks"]
    }
  )();
}
