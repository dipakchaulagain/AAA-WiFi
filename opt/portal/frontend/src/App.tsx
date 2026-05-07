import React from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import Setup from "./pages/Setup";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Sessions from "./pages/Sessions";
import Accounting from "./pages/Accounting";
import Users from "./pages/Users";
import UserDetail from "./pages/UserDetail";
import Policy from "./pages/Policy";
import Diagnostics from "./pages/Diagnostics";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { api } from "./api/client";

type SetupStatus = { setup_complete: boolean };

export default function App() {
  const [setupComplete, setSetupComplete] = React.useState<boolean | null>(null);
  const nav = useNavigate();
  const loc = useLocation();

  React.useEffect(() => {
    let alive = true;
    api
      .get<SetupStatus>("/setup/status", { baseURL: "/api/v1" })
      .then((r) => {
        if (!alive) return;
        setSetupComplete(r.data.setup_complete);
      })
      .catch(() => {
        if (!alive) return;
        setSetupComplete(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  React.useEffect(() => {
    if (setupComplete === null) return;
    if (!setupComplete && loc.pathname !== "/setup") nav("/setup", { replace: true });
    if (setupComplete && loc.pathname === "/setup") nav("/", { replace: true });
  }, [setupComplete, loc.pathname, nav]);

  if (setupComplete === null) {
    return (
      <div className="min-h-screen grid place-items-center">
        <div className="text-sm text-slate-600">Loading…</div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/setup" element={<Setup />} />
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="sessions" element={<Sessions />} />
        <Route path="accounting" element={<Accounting />} />
        <Route path="users" element={<Users />} />
        <Route path="users/local/:id" element={<UserDetail />} />
        <Route path="policy" element={<Policy />} />
        <Route path="diagnostics" element={<Diagnostics />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

