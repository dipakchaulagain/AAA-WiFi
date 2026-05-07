import React from "react";
import DataTable from "../components/DataTable";
import { exportAccountingCsv, getAccounting } from "../api/accounting";
import { listNas } from "../api/policy";

export default function Accounting() {
  const [nasList, setNasList] = React.useState<any[]>([]);
  const [q, setQ] = React.useState<any>({ page: 1, per_page: 50 });
  const [data, setData] = React.useState<any>(null);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    listNas().then(setNasList).catch(() => setNasList([]));
  }, []);

  async function load(nextQ = q) {
    setErr(null);
    try {
      setData(await getAccounting(nextQ));
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to load accounting.");
    }
  }

  React.useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="font-medium">Accounting logs</div>
        <button onClick={() => exportAccountingCsv(q)} className="text-sm px-3 py-1.5 rounded border hover:bg-slate-50">
          Export CSV
        </button>
      </div>

      <div className="mt-3 bg-white border rounded p-3 grid grid-cols-1 md:grid-cols-5 gap-2 text-sm">
        <input
          className="border rounded px-2 py-1.5"
          placeholder="Username"
          value={q.username ?? ""}
          onChange={(e) => setQ((s: any) => ({ ...s, username: e.target.value }))}
        />
        <select className="border rounded px-2 py-1.5" value={q.nas_ip ?? ""} onChange={(e) => setQ((s: any) => ({ ...s, nas_ip: e.target.value || undefined }))}>
          <option value="">NAS IP (all)</option>
          {nasList.map((n) => (
            <option key={n.id} value={n.nasname}>
              {n.nasname} ({n.shortname})
            </option>
          ))}
        </select>
        <input className="border rounded px-2 py-1.5" type="date" value={q.from_date ?? ""} onChange={(e) => setQ((s: any) => ({ ...s, from_date: e.target.value || undefined }))} />
        <input className="border rounded px-2 py-1.5" type="date" value={q.to_date ?? ""} onChange={(e) => setQ((s: any) => ({ ...s, to_date: e.target.value || undefined }))} />
        <input
          className="border rounded px-2 py-1.5"
          placeholder="SSID contains…"
          value={q.ssid ?? ""}
          onChange={(e) => setQ((s: any) => ({ ...s, ssid: e.target.value }))}
        />
        <div className="md:col-span-5 flex gap-2 justify-end">
          <button
            onClick={() => {
              const next = { ...q, page: 1 };
              setQ(next);
              load(next);
            }}
            className="px-3 py-1.5 rounded bg-slate-900 text-white hover:bg-slate-800"
          >
            Apply
          </button>
          <button
            onClick={() => {
              const next = { page: 1, per_page: 50 };
              setQ(next);
              load(next);
            }}
            className="px-3 py-1.5 rounded border hover:bg-slate-50"
          >
            Reset
          </button>
        </div>
      </div>

      {err && <div className="mt-2 text-sm text-rose-700">{err}</div>}
      {!data ? (
        <div className="mt-3 text-sm text-slate-600">Loading…</div>
      ) : (
        <div className="mt-3 space-y-2">
          <DataTable
            rows={data.items}
            columns={[
              { key: "username", header: "Username" },
              { key: "nasipaddress", header: "NAS" },
              { key: "calledstationid", header: "SSID" },
              { key: "callingstationid", header: "MAC" },
              { key: "acctstarttime", header: "Start" },
              { key: "acctstoptime", header: "Stop" },
              { key: "acctsessiontime", header: "Duration (s)" },
            ]}
          />
          <div className="flex items-center justify-between text-sm">
            <div className="text-slate-600">
              Total: {data.total} • Page {data.page}
            </div>
            <div className="flex gap-2">
              <button
                disabled={data.page <= 1}
                onClick={() => {
                  const next = { ...q, page: data.page - 1 };
                  setQ(next);
                  load(next);
                }}
                className="px-3 py-1.5 rounded border hover:bg-slate-50 disabled:opacity-50"
              >
                Prev
              </button>
              <button
                disabled={data.page * data.per_page >= data.total}
                onClick={() => {
                  const next = { ...q, page: data.page + 1 };
                  setQ(next);
                  load(next);
                }}
                className="px-3 py-1.5 rounded border hover:bg-slate-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

