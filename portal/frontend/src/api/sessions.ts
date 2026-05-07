import { api } from "./client";

export async function getActiveSessions() {
  const { data } = await api.get("/sessions/active");
  return data as any[];
}

export async function disconnectSession(id: number) {
  const { data } = await api.delete(`/sessions/${id}`);
  return data as { success: boolean };
}

