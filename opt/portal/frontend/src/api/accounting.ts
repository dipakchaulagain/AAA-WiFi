import { api } from "./client";

export type AccountingQuery = {
  username?: string;
  nas_ip?: string;
  ssid?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
};

export async function getAccounting(q: AccountingQuery) {
  const { data } = await api.get("/accounting", { params: q });
  return data as { page: number; per_page: number; total: number; items: any[] };
}

export function exportAccountingCsv(q: AccountingQuery) {
  const params = new URLSearchParams(q as any).toString();
  window.location.href = `/api/v1/accounting/export?${params}`;
}

