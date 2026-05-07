import React from "react";
import DataTable from "../components/DataTable";
import ConfirmDialog from "../components/ConfirmDialog";
import { disconnectSession, getActiveSessions } from "../api/sessions";

function fmtDuration(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export default function Sessions() {
  const [rows, setRows] = React.useState<any[]>([]);
  const [err, setErr] = React.useState<string | null>(null);
  const [confirmId, setConfirmId] = React.useState<number | null>(null);

  async function load() {
    setErr(null);
    try {
      setRows(await getActiveSessions());
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to load sessions.");
    }
  }

  React.useEffect(() => {
    load();
  }, []);

  async function doDisconnect() {
    if (confirmId == null) return;
    try {
      await disconnectSession(confirmId);
      setConfirmId(null);
      load();
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Disconnect failed.");
      setConfirmId(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="font-medium">Active sessions</div>
        <button onClick={load} className="text-sm px-3 py-1.5 rounded border hover:bg-slate-50">
          Refresh
        </button>
      </div>
      {err && <div className="mt-2 text-sm text-rose-700">{err}</div>}

      <div className="mt-3">
        <DataTable
          rows={rows}
          columns={[
            { key: "username", header: "Username" },
            { key: "callingstationid", header: "MAC" },
            { key: "nasipaddress", header: "NAS IP" },
            { key: "calledstationid", header: "SSID" },
            { key: "framedipaddress", header: "IP" },
            { key: "acctstarttime", header: "Start" },
            {
              key: "duration_seconds",
              header: "Duration",
              render: (r) => fmtDuration(Number(r.duration_seconds || 0)),
            },
            {
              key: "actions",
              header: "Actions",
              render: (r) => (
                <button
                  onClick={() => setConfirmId(Number(r.radacctid))}
                  className="text-sm px-2 py-1 rounded bg-rose-600 text-white hover:bg-rose-700"
                >
                  Disconnect
                </button>
              ),
            },
          ]}
        />
      </div>

      <ConfirmDialog
        open={confirmId != null}
        title="Disconnect session?"
        message="This will send a RADIUS Disconnect-Request (CoA) to the controller."
        confirmText="Disconnect"
        onCancel={() => setConfirmId(null)}
        onConfirm={doDisconnect}
      />
    </div>
  );
}

