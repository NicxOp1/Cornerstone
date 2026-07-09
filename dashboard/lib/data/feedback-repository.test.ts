import { describe, expect, it } from "vitest";
import { FeedbackRepository } from "./feedback-repository";
import { FakeSheetsWriteClient } from "./test-helpers/fake-sheets-write-client";

const HEADERS = ["id", "call_id", "timestamp", "comment", "status", "reply", "replied_at"];

describe("FeedbackRepository.addFeedback", () => {
  it("agrega una fila nueva con status open", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Feedback", HEADERS);
    const repo = new FeedbackRepository(client);

    const entry = await repo.addFeedback("call_1", "Por que no se agendo esto?");

    expect(entry.callId).toBe("call_1");
    expect(entry.status).toBe("open");
    expect(entry.id).toBeTruthy();
  });
});

describe("FeedbackRepository.addReply", () => {
  it("completa reply y pasa a resuelto sin perder el comentario original", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Feedback", HEADERS);
    const repo = new FeedbackRepository(client);
    const created = await repo.addFeedback("call_1", "Comentario original");

    const updated = await repo.addReply(created.id, "Ya lo revisamos, fue un error del agente.");

    expect(updated).toBe(true);
    const stored = await repo.getFeedbackForCall("call_1");
    expect(stored[0].comment).toBe("Comentario original");
    expect(stored[0].reply).toBe("Ya lo revisamos, fue un error del agente.");
    expect(stored[0].status).toBe("resuelto");
  });

  it("devuelve false si el id no existe", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Feedback", HEADERS);
    const repo = new FeedbackRepository(client);

    const updated = await repo.addReply("id-inexistente", "respuesta");

    expect(updated).toBe(false);
  });
});

describe("FeedbackRepository.getFeedbackForCall", () => {
  it("filtra solo el feedback de la llamada pedida", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Feedback", HEADERS);
    const repo = new FeedbackRepository(client);
    await repo.addFeedback("call_1", "sobre call 1");
    await repo.addFeedback("call_2", "sobre call 2");

    const result = await repo.getFeedbackForCall("call_1");

    expect(result).toHaveLength(1);
    expect(result[0].comment).toBe("sobre call 1");
  });
});
