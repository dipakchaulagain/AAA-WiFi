import React from "react";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import {
  blockLdapUser,
  blockLocalUser,
  createLocalUser,
  deleteLocalUser,
  listLdapUsers,
  listLocalUsers,
  unblockLdapUser,
  unblockLocalUser,
} from "../api/users";

export default function Users() {
  const [tab, setTab] = React.useState<"local" | "ldap">("local");
  const [local, setLocal] = React.useState<any[]>([]);
  const [ldap, setLdap] = React.useState<any[]>([]);
  const [err, setErr] = React.useState<string | null>(null);
  const [confirm, setConfirm] = React.useState<{ type: string; username: string } | null>(null);

  const [newUser, setNewUser] = React.useState({ username: "", password: "", simultaneous_use: 2 });

  async function load() {
    setErr(null);
    try {
      if (tab === "local") setLocal(await listLocalUsers());
      else setLdap(await listLdapUsers());
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to load users.");
    }
  }

  React.useEffect(() => {
    load();
  }, [tab]);

  async function addLocal() {
    setErr(null);
    try {
      await createLocalUser(newUser);
      setNewUser({ username: "", password: "", simultaneous_use: 2 });
      load();
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Failed to create user.");
    }
  }

  async function doConfirm() {
    if (!confirm) return;
    setErr(null);
    try {
      if (confirm.type === "local.delete") await deleteLocalUser(confirm.username);
      if (confirm.type === "local.block") await blockLocalUser(confirm.username);
      if (confirm.type === "local.unblock") await unblockLocalUser(confirm.username);
      if (confirm.type === "ldap.block") await blockLdapUser(confirm.username);
      if (confirm.type === "ldap.unblock") await unblockLdapUser(confirm.username);
      setConfirm(null);
      load();
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Operation failed.");
      setConfirm(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="font-medium">Users</div>
        <button onClick={load} className="text-sm px-3 py-1.5 rounded border hover:bg-slate-50">
          Refresh
        </button>
      </div>

      <div className="mt-3 flex gap-2">
        <button
          onClick={() => setTab("local")}
          className={`px-3 py-1.5 rounded text-sm border ${tab === "local" ? "bg-slate-900 text-white border-slate-900" : "bg-white"}`}
        >
          Local
        </button>
        <button
          onClick={() => setTab("ldap")}
          className={`px-3 py-1.5 rounded text-sm border ${tab === "ldap" ? "bg-slate-900 text-white border-slate-900" : "bg-white"}`}
        >
          LDAP
        </button>
      </div>

      {err && <div className="mt-3 text-sm text-rose-700">{err}</div>}

      {tab === "local" && (
        <div className="mt-3 space-y-3">
          <div className="bg-white border rounded p-3 grid grid-cols-1 md:grid-cols-4 gap-2 text-sm">
            <input className="border rounded px-2 py-1.5" placeholder="Username" value={newUser.username} onChange={(e) => setNewUser((s) => ({ ...s, username: e.target.value }))} />
            <input className="border rounded px-2 py-1.5" placeholder="Password" type="password" value={newUser.password} onChange={(e) => setNewUser((s) => ({ ...s, password: e.target.value }))} />
            <select className="border rounded px-2 py-1.5" value={newUser.simultaneous_use} onChange={(e) => setNewUser((s) => ({ ...s, simultaneous_use: Number(e.target.value) }))}>
              <option value={1}>1 device</option>
              <option value={2}>2 devices</option>
            </select>
            <button onClick={addLocal} className="px-3 py-1.5 rounded bg-emerald-600 text-white hover:bg-emerald-700">
              Add user
            </button>
          </div>

          <DataTable
            rows={local}
            columns={[
              { key: "username", header: "Username", render: (r) => <Link className="text-slate-900 underline" to={`/users/local/${encodeURIComponent(r.username)}`}>{r.username}</Link> },
              { key: "simultaneous_use", header: "Simultaneous-Use" },
              { key: "blocked", header: "Status", render: (r) => <StatusBadge ok={!r.blocked} text={r.blocked ? "Blocked" : "Active"} /> },
              { key: "last_seen", header: "Last seen" },
              {
                key: "actions",
                header: "Actions",
                render: (r) => (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfirm({ type: r.blocked ? "local.unblock" : "local.block", username: r.username })}
                      className={`px-2 py-1 rounded text-sm ${r.blocked ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"}`}
                    >
                      {r.blocked ? "Unblock" : "Block"}
                    </button>
                    <button onClick={() => setConfirm({ type: "local.delete", username: r.username })} className="px-2 py-1 rounded text-sm border hover:bg-slate-50">
                      Delete
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      {tab === "ldap" && (
        <div className="mt-3">
          <DataTable
            rows={ldap}
            columns={[
              { key: "displayName", header: "Name" },
              { key: "sAMAccountName", header: "Username" },
              { key: "mail", header: "Email" },
              { key: "current_sessions", header: "Sessions" },
              { key: "last_seen", header: "Last seen" },
              { key: "blocked", header: "Status", render: (r) => <StatusBadge ok={!r.blocked} text={r.blocked ? "Blocked" : "Active"} /> },
              {
                key: "actions",
                header: "Actions",
                render: (r) => (
                  <button
                    onClick={() => setConfirm({ type: r.blocked ? "ldap.unblock" : "ldap.block", username: r.sAMAccountName })}
                    className={`px-2 py-1 rounded text-sm ${r.blocked ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"}`}
                  >
                    {r.blocked ? "Unblock" : "Block"}
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      <ConfirmDialog
        open={!!confirm}
        title="Confirm action"
        message={`Proceed with ${confirm?.type.replace(".", " ")} for ${confirm?.username}?`}
        onCancel={() => setConfirm(null)}
        onConfirm={doConfirm}
      />
    </div>
  );
}

