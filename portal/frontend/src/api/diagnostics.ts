import { api } from "./client";

export async function testAuth(username: string, password: string) {
  const { data } = await api.post("/diagnostics/test-auth", { username, password });
  return data as { success: boolean; output: string };
}

export async function testLdap() {
  const { data } = await api.post("/diagnostics/test-ldap");
  return data as any;
}

export function logStreamUrl() {
  return "/api/v1/diagnostics/log-stream";
}

