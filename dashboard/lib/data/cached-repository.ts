import { unstable_cache } from "next/cache";
import type { CallFilters } from "@/lib/data/repository";
import { FeedbackRepository } from "@/lib/data/feedback-repository";
import { MessagesRepository } from "@/lib/data/messages-repository";
import { buildProductionRepository } from "@/lib/data/sheets-repository";
import { buildWriteClient } from "@/lib/data/sheets-writer";

const repository = buildProductionRepository();
const writeClient = buildWriteClient();
const feedbackRepository = new FeedbackRepository(writeClient);
const messagesRepository = new MessagesRepository(writeClient);

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
