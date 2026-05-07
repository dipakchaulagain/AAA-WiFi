import { api } from "./client";

export async function getDashboardSummary() {
  const { data } = await api.get("/dashboard/summary");
  return data as {
    metrics: {
      active_sessions: number;
      auth_attempts_last_hour: number;
      failed_auths_last_hour: number;
      blocked_users: number;
    };
    recent_sessions: any[];
  };
}

