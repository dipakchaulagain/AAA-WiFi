import React from "react";
import DataTable from "../components/DataTable";
import { getDashboardSummary } from "../api/dashboard";

function Card({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="bg-white border rounded p-4">
      <div className="text-xs text-slate-600">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = React.useState<any>(null);
  const [err, setErr] = React.useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = React.useState<Date | null>(null);

  async function load() {
    setErr(null);
    try {
      const d = await getDashboardSummary();
      setData(d);
      setUpdatedAt(new Date());
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to load dashboard.");
    }
  }

  React.useEffect(() => {
    load();
    const t = window.setInterval(load, 30_000);
    return () => window.clearInterval(t);
  }, []);

  if (err) return <div className="text-sm text-rose-700">{err}</div>;
  if (!data) return <div className="text-sm text-slate-600">Loading…</div>;

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Card label="Active sessions" value={data.metrics.active_sessions} />
        <Card label="Auth attempts (last hour)" value={data.metrics.auth_attempts_last_hour} />
        <Card label="Failed auths (last hour)" value={data.metrics.failed_auths_last_hour} />
        <Card label="Blocked users" value={data.metrics.blocked_users} />
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div className="font-medium">Recently active sessions</div>
        <div className="text-xs text-slate-500">
          Last updated: {updatedAt ? updatedAt.toLocaleTimeString() : "—"}
        </div>
      </div>

      <div className="mt-2">
        <DataTable
          rows={data.recent_sessions}
          columns={[
            { key: "username", header: "Username" },
            { key: "nasipaddress", header: "NAS IP" },
            { key: "calledstationid", header: "SSID" },
            { key: "acctstarttime", header: "Start" },
            { key: "duration_seconds", header: "Duration (s)" },
          ]}
        />
      </div>
    </div>
  );
}

