import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api/client";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/sessions", label: "Sessions" },
  { to: "/accounting", label: "Accounting" },
  { to: "/users", label: "Users" },
  { to: "/policy", label: "Policy" },
  { to: "/diagnostics", label: "Diagnostics" },
];

export default function Layout() {
  const nav = useNavigate();
  const [busy, setBusy] = React.useState(false);

  async function logout() {
    setBusy(true);
    try {
      await api.post("/auth/logout", {}, { baseURL: "/api/v1" });
      nav("/login", { replace: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-slate-900 text-slate-100 p-4 hidden md:block">
        <div className="font-semibold tracking-tight text-lg">Wi‑Fi AAA</div>
        <nav className="mt-6 space-y-1">
          {navItems.map((i) => (
            <NavLink
              key={i.to}
              to={i.to}
              end={i.to === "/"}
              className={({ isActive }) =>
                `block px-3 py-2 rounded text-sm ${
                  isActive ? "bg-slate-700" : "hover:bg-slate-800 text-slate-200"
                }`
              }
            >
              {i.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1">
        <div className="h-14 bg-white border-b flex items-center justify-between px-4">
          <div className="text-sm text-slate-600">AAA Management Portal</div>
          <button
            onClick={logout}
            disabled={busy}
            className="text-sm px-3 py-1.5 rounded border hover:bg-slate-50 disabled:opacity-50"
          >
            {busy ? "Logging out…" : "Logout"}
          </button>
        </div>
        <div className="p-4">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

