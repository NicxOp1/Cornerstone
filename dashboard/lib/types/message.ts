export type MessageSender = "john" | "equipo";

export interface MessageEntry {
  id: string;
  timestamp: string;
  sender: MessageSender;
  text: string;
  readByEquipo: boolean;
  readByJohn: boolean;
}
