import { api } from "./client";

export async function listLocalUsers() {
  const { data } = await api.get("/users/local");
  return data as any[];
}

export async function createLocalUser(payload: { username: string; password: string; simultaneous_use?: number }) {
  const { data } = await api.post("/users/local", payload);
  return data as { success: boolean };
}

export async function updateLocalUser(username: string, payload: { password?: string; simultaneous_use?: number }) {
  const { data } = await api.put(`/users/local/${encodeURIComponent(username)}`, payload);
  return data as { success: boolean };
}

export async function deleteLocalUser(username: string) {
  const { data } = await api.delete(`/users/local/${encodeURIComponent(username)}`);
  return data as { success: boolean };
}

export async function blockLocalUser(username: string, reason?: string) {
  const { data } = await api.post(`/users/local/${encodeURIComponent(username)}/block`, { reason });
  return data as { success: boolean };
}

export async function unblockLocalUser(username: string) {
  const { data } = await api.post(`/users/local/${encodeURIComponent(username)}/unblock`);
  return data as { success: boolean };
}

export async function listLdapUsers() {
  const { data } = await api.get("/users/ldap");
  return data as any[];
}

export async function blockLdapUser(username: string, reason?: string) {
  const { data } = await api.post(`/users/ldap/${encodeURIComponent(username)}/block`, { reason });
  return data as { success: boolean };
}

export async function unblockLdapUser(username: string) {
  const { data } = await api.post(`/users/ldap/${encodeURIComponent(username)}/unblock`);
  return data as { success: boolean };
}

