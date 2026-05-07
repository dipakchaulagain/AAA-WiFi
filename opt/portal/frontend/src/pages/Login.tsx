import React from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function Login() {
  const nav = useNavigate();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [err, setErr] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await api.post("/auth/login", { username, password }, { baseURL: "/api/v1" });
      nav("/", { replace: true });
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-4">
      <form onSubmit={submit} className="bg-white border rounded shadow-sm p-6 w-full max-w-sm">
        <div className="font-semibold text-lg">Portal login</div>
        <div className="text-sm text-slate-600 mt-1">Sign in to manage Wi‑Fi AAA.</div>

        <label className="block mt-4 text-sm">
          <div className="text-slate-700">Username</div>
          <input
            className="mt-1 w-full border rounded px-3 py-2"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </label>

        <label className="block mt-3 text-sm">
          <div className="text-slate-700">Password</div>
          <input
            className="mt-1 w-full border rounded px-3 py-2"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>

        {err && <div className="mt-3 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded p-2">{err}</div>}

        <button
          disabled={busy}
          className="mt-4 w-full bg-slate-900 text-white rounded px-3 py-2 text-sm hover:bg-slate-800 disabled:opacity-50"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

