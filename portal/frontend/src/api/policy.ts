import { api } from "./client";

export async function getPolicy() {
  const { data } = await api.get("/policy");
  return data as { config: any; nas: any[] };
}

export async function updatePolicy(payload: any) {
  const { data } = await api.put("/policy", payload);
  return data as { success: boolean };
}

export async function listNas() {
  const { data } = await api.get("/nas");
  return data as any[];
}

export async function createNas(payload: any) {
  const { data } = await api.post("/nas", payload);
  return data as { success: boolean };
}

export async function updateNas(id: number, payload: any) {
  const { data } = await api.put(`/nas/${id}`, payload);
  return data as { success: boolean };
}

export async function deleteNas(id: number) {
  const { data } = await api.delete(`/nas/${id}`);
  return data as { success: boolean };
}

