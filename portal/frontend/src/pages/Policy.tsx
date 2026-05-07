import React from "react";
import DataTable from "../components/DataTable";
import { createNas, deleteNas, getPolicy, updatePolicy } from "../api/policy";

export default function Policy() {
  const [data, setData] = React.useState<any>(null);
  const [err, setErr] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  const [nasForm, setNasForm] = React.useState({ shortname: "", nasname: "", secret: "", description: "" });

  async function load() {
    setErr(null);
    try {
      setData(await getPolicy());
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to load policy.");
    }
  }

  React.useEffect(() => {
    load();
  }, []);

  async function saveGlobal() {
    setBusy(true);
    setErr(null);
    try {
      await updatePolicy({
        auth_mode: data.config.auth_mode,
        default_simultaneous_use: Number(data.config.default_simultaneous_use || 2),
        ldap_group_dn: data.config.ldap_group_dn,
      });
      await load();
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  async function addNas() {
    setBusy(true);
    setErr(null);
    try {
      await createNas(nasForm);
      setNasForm({ shortname: "", nasname: "", secret: "", description: "" });
      await load();
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to add NAS.");
    } finally {
      setBusy(false);
    }
  }

  async function removeNas(id: number) {
    setBusy(true);
    setErr(null);
    try {
      await deleteNas(id);
      await load();
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to delete NAS.");
    } finally {
      setBusy(false);
    }
  }

  if (err) return <div className="text-sm text-rose-700">{err}</div>;
  if (!data) return <div className="text-sm text-slate-600">Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white border rounded p-4">
        <div className="font-medium">Global policy</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3 text-sm">
          <label>
            <div className="text-slate-700">Auth mode</div>
            <select
              className="mt-1 w-full border rounded px-3 py-2"
              value={data.config.auth_mode || "db"}
              onChange={(e) => setData((s: any) => ({ ...s, config: { ...s.config, auth_mode: e.target.value } }))}
            >
              <option value="db">db</option>
              <option value="ldap">ldap</option>
              <option value="hybrid">hybrid</option>
            </select>
          </label>
          <label>
            <div className="text-slate-700">Default simultaneous-use</div>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              type="number"
              min={1}
              max={10}
              value={data.config.default_simultaneous_use || 2}
              onChange={(e) => setData((s: any) => ({ ...s, config: { ...s.config, default_simultaneous_use: e.target.value } }))}
            />
          </label>
          <label className="md:col-span-3">
            <div className="text-slate-700">LDAP group DN</div>
            <input
              className="mt-1 w-full border rounded px-3 py-2"
              value={data.config.ldap_group_dn || ""}
              onChange={(e) => setData((s: any) => ({ ...s, config: { ...s.config, ldap_group_dn: e.target.value } }))}
            />
          </label>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            onClick={saveGlobal}
            disabled={busy}
            className="px-3 py-2 text-sm rounded bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {busy ? "Saving…" : "Save & reload"}
          </button>
        </div>
      </div>

      <div className="bg-white border rounded p-4">
        <div className="font-medium">NAS / Controller list</div>
        <div className="mt-3">
          <DataTable
            rows={data.nas}
            columns={[
              { key: "shortname", header: "Shortname" },
              { key: "nasname", header: "IP" },
              { key: "description", header: "Description" },
              {
                key: "actions",
                header: "Actions",
                render: (r) => (
                  <button
                    disabled={busy}
                    onClick={() => removeNas(Number(r.id))}
                    className="px-2 py-1 rounded text-sm border hover:bg-slate-50 disabled:opacity-50"
                  >
                    Delete
                  </button>
                ),
              },
            ]}
          />
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-2 text-sm">
          <input className="border rounded px-2 py-1.5" placeholder="shortname" value={nasForm.shortname} onChange={(e) => setNasForm((s) => ({ ...s, shortname: e.target.value }))} />
          <input className="border rounded px-2 py-1.5" placeholder="IP" value={nasForm.nasname} onChange={(e) => setNasForm((s) => ({ ...s, nasname: e.target.value }))} />
          <input className="border rounded px-2 py-1.5" placeholder="secret" value={nasForm.secret} onChange={(e) => setNasForm((s) => ({ ...s, secret: e.target.value }))} />
          <button onClick={addNas} disabled={busy} className="px-3 py-1.5 rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50">
            Add NAS
          </button>
          <input className="border rounded px-2 py-1.5 md:col-span-4" placeholder="description" value={nasForm.description} onChange={(e) => setNasForm((s) => ({ ...s, description: e.target.value }))} />
        </div>
      </div>
    </div>
  );
}

