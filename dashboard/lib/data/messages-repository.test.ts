import { describe, expect, it } from "vitest";
import { MessagesRepository } from "./messages-repository";
import { FakeSheetsWriteClient } from "./test-helpers/fake-sheets-write-client";

const HEADERS = ["id", "timestamp", "sender", "text", "read_by_equipo", "read_by_john"];

describe("MessagesRepository.addMessage", () => {
  it("un mensaje de john queda leido por john pero no por el equipo", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Messages", HEADERS);
    const repo = new MessagesRepository(client);

    const entry = await repo.addMessage("john", "Hola, alguien?");

    expect(entry.readByJohn).toBe(true);
    expect(entry.readByEquipo).toBe(false);
  });

  it("un mensaje del equipo queda leido por el equipo pero no por john", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Messages", HEADERS);
    const repo = new MessagesRepository(client);

    const entry = await repo.addMessage("equipo", "Ya te respondemos");

    expect(entry.readByEquipo).toBe(true);
    expect(entry.readByJohn).toBe(false);
  });
});

describe("MessagesRepository.countUnreadForEquipo", () => {
  it("cuenta solo los mensajes de john sin leer por el equipo", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Messages", HEADERS);
    const repo = new MessagesRepository(client);
    await repo.addMessage("john", "mensaje 1");
    await repo.addMessage("john", "mensaje 2");
    await repo.addMessage("equipo", "respuesta");

    expect(await repo.countUnreadForEquipo()).toBe(2);
  });
});

describe("MessagesRepository.markAllReadByEquipo", () => {
  it("marca todos los mensajes sin leer como leidos", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Messages", HEADERS);
    const repo = new MessagesRepository(client);
    await repo.addMessage("john", "mensaje 1");
    await repo.addMessage("john", "mensaje 2");

    await repo.markAllReadByEquipo();

    expect(await repo.countUnreadForEquipo()).toBe(0);
  });

  it("no rompe el texto de mensajes que ya estaban leidos", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Messages", HEADERS);
    const repo = new MessagesRepository(client);
    await repo.addMessage("equipo", "ya leido por equipo al crearse");

    await repo.markAllReadByEquipo();

    const messages = await repo.listMessages();
    expect(messages[0].text).toBe("ya leido por equipo al crearse");
  });
});

describe("MessagesRepository.listMessages", () => {
  it("devuelve los mensajes en el orden en que se guardaron", async () => {
    const client = new FakeSheetsWriteClient();
    client.seed("Messages", HEADERS);
    const repo = new MessagesRepository(client);
    await repo.addMessage("john", "primero");
    await repo.addMessage("equipo", "segundo");

    const messages = await repo.listMessages();

    expect(messages.map((message) => message.text)).toEqual(["primero", "segundo"]);
  });
});
