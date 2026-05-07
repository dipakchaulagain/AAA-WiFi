import React from "react";
import { useParams } from "react-router-dom";
import { blockLocalUser, unblockLocalUser, updateLocalUser } from "../api/users";

export default function UserDetail() {
  const { id } = useParams();
  const username = decodeURIComponent(id || "");

  const [password, setPassword] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [sim, setSim] = React.useState<number | "">("");
  const [blocked, setBlocked] = React.useState<boolean>(false);
  const [err, setErr] = React.useState<string | null>(null);
  const [ok, setOk] = React.useState<string | null>(null);

  async function save() {
    setErr(null);
    setOk(null);
    try {
      if (password && password !== confirm) throw new Error("Passwords do not match.");
      await updateLocalUser(username, {
        password: password || undefined,
        simultaneous_use: sim === "" ? undefined : sim,
      });
      setOk("Saved.");
      setPassword("");
      setConfirm("");
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? e?.message ?? "Save failed.");
    }
  }

  async function toggleBlock() {
    setErr(null);
    setOk(null);
    try {
      if (blocked) await unblockLocalUser(username);
      else await blockLocalUser(username);
      setBlocked((b) => !b);
      setOk(blocked ? "Unblocked." : "Blocked.");
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Operation failed.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="font-medium">Local user: {username}</div>

      <div className="bg-white border rounded p-4">
        <div className="font-medium text-sm">Update credentials / policy</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 text-sm">
          <label>
            <div className="text-slate-700">New password</div>
            <input className="mt-1 w-full border rounded px-3 py-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          <label>
            <div className="text-slate-700">Confirm</div>
            <input className="mt-1 w-full border rounded px-3 py-2" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </label>
          <label>
            <div className="text-slate-700">Simultaneous-Use override</div>
            <select className="mt-1 w-full border rounded px-3 py-2" value={sim} onChange={(e) => setSim(e.target.value ? Number(e.target.value) : "")}>
              <option value="">Use global default</option>
              <option value="1">1 device</option>
              <option value="2">2 devices</option>
            </select>
          </label>
          <div className="flex items-end gap-2">
            <button onClick={save} className="px-3 py-2 text-sm rounded bg-slate-900 text-white hover:bg-slate-800">
              Save
            </button>
            <button
              onClick={toggleBlock}
              className={`px-3 py-2 text-sm rounded ${blocked ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"}`}
            >
              {blocked ? "Unblock" : "Block"}
            </button>
          </div>
        </div>
        {err && <div className="mt-3 text-sm text-rose-700">{err}</div>}
        {ok && <div className="mt-3 text-sm text-emerald-700">{ok}</div>}
      </div>

      <div className="text-xs text-slate-600">
        Auth history and per-session controls can be added by extending backend endpoints for `radpostauth` and per-user sessions.
      </div>
    </div>
  );
}

