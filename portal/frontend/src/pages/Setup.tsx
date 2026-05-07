import React from "react";
import { api } from "../api/client";

type AuthMode = "db" | "ldap" | "hybrid";

function StepPills({ step, labels }: { step: number; labels: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {labels.map((l, i) => {
        const active = i === step;
        const done = i < step;
        return (
          <div
            key={l}
            className={`px-3 py-1 rounded-full text-xs border ${
              active ? "bg-slate-900 text-white border-slate-900" : done ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-white text-slate-600"
            }`}
          >
            {l}
          </div>
        );
      })}
    </div>
  );
}

export default function Setup() {
  const [step, setStep] = React.useState(0);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  const [authMode, setAuthMode] = React.useState<AuthMode>("db");
  const includesLdap = authMode !== "db";

  const [ldap, setLdap] = React.useState({
    ldap_server: "ldaps://dc.domain.com",
    ldap_bind_dn: "",
    ldap_bind_pw: "",
    ldap_base_dn: "",
    ldap_group_dn: "",
    ldap_user_filter: "((&(objectClass=user)(sAMAccountName=%u)))",
  });

  const [radius, setRadius] = React.useState({
    radius_shared_secret: "",
    ac_ip: "",
    ac_shortname: "huawei-ac",
    ac_description: "",
  });

  const [eap, setEap] = React.useState({ eap_cert_path: "" });

  const [admin, setAdmin] = React.useState({ admin_username: "admin", admin_password: "", confirm: "" });

  const steps = ["Auth mode", "LDAP", "RADIUS/AC", "EAP cert", "Admin"];

  function next() {
    setErr(null);
    if (step === 0) return setStep(includesLdap ? 1 : 2);
    if (step === 1) return setStep(2);
    if (step === 2) return setStep(3);
    if (step === 3) return setStep(4);
  }

  function back() {
    setErr(null);
    if (step === 4) return setStep(3);
    if (step === 3) return setStep(2);
    if (step === 2) return setStep(includesLdap ? 1 : 0);
    if (step === 1) return setStep(0);
  }

  async function testLdap() {
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/setup/test-ldap", ldap, { baseURL: "/api/v1" });
      if (!data?.success) throw new Error(data?.error || "LDAP test failed.");
    } catch (e: any) {
      setErr(e?.message ?? "LDAP test failed.");
      return;
    } finally {
      setBusy(false);
    }
    next();
  }

  async function complete() {
    setBusy(true);
    setErr(null);
    try {
      if (admin.admin_password !== admin.confirm) throw new Error("Admin passwords do not match.");
      const payload: any = {
        auth_mode: authMode,
        ...radius,
        ...eap,
        admin_username: admin.admin_username,
        admin_password: admin.admin_password,
      };
      if (includesLdap) Object.assign(payload, ldap);
      await api.post("/setup/init", payload, { baseURL: "/api/v1" });
      window.location.href = "/login";
    } catch (e: any) {
      setErr(e?.response?.data?.detail?.detail ?? e?.message ?? "Setup failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen p-6 max-w-3xl mx-auto">
      <div className="text-xl font-semibold">First‑run setup</div>
      <div className="text-sm text-slate-600 mt-1">Configure authentication, LDAP, and RADIUS integration.</div>

      <div className="mt-4">
        <StepPills step={step} labels={steps} />
      </div>

      <div className="mt-6 bg-white border rounded p-4">
        {step === 0 && (
          <div>
            <div className="font-medium">Authentication mode</div>
            <div className="mt-3 space-y-2 text-sm">
              <label className="flex items-center gap-2">
                <input type="radio" checked={authMode === "db"} onChange={() => setAuthMode("db")} />
                Local DB only
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" checked={authMode === "ldap"} onChange={() => setAuthMode("ldap")} />
                LDAP / Active Directory only
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" checked={authMode === "hybrid"} onChange={() => setAuthMode("hybrid")} />
                Hybrid (DB + LDAP fallback)
              </label>
            </div>
          </div>
        )}

        {step === 1 && (
          <div>
            <div className="font-medium">LDAP connection (LDAPS)</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 text-sm">
              {Object.entries(ldap).map(([k, v]) => (
                <label key={k} className={k === "ldap_user_filter" ? "md:col-span-2" : ""}>
                  <div className="text-slate-700">{k}</div>
                  <input
                    className="mt-1 w-full border rounded px-3 py-2"
                    value={v}
                    onChange={(e) => setLdap((s) => ({ ...s, [k]: e.target.value }))}
                  />
                </label>
              ))}
            </div>
            <div className="mt-4">
              <button
                disabled={busy}
                onClick={testLdap}
                className="px-3 py-2 text-sm rounded bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {busy ? "Testing…" : "Test connection & continue"}
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <div className="font-medium">RADIUS / AC settings</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 text-sm">
              {Object.entries(radius).map(([k, v]) => (
                <label key={k} className={k === "ac_description" ? "md:col-span-2" : ""}>
                  <div className="text-slate-700">{k}</div>
                  <input
                    className="mt-1 w-full border rounded px-3 py-2"
                    value={v}
                    onChange={(e) => setRadius((s) => ({ ...s, [k]: e.target.value }))}
                  />
                </label>
              ))}
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <div className="font-medium">EAP certificate</div>
            <div className="text-sm text-slate-600 mt-1">
              For production, provide a valid certificate path (PEM). Self‑signed generation can be added via backend automation.
            </div>
            <label className="block mt-3 text-sm">
              <div className="text-slate-700">Existing cert path (PEM)</div>
              <input
                className="mt-1 w-full border rounded px-3 py-2"
                value={eap.eap_cert_path}
                onChange={(e) => setEap({ eap_cert_path: e.target.value })}
                placeholder="/etc/freeradius/3.0/certs/server.pem"
              />
            </label>
          </div>
        )}

        {step === 4 && (
          <div>
            <div className="font-medium">Admin account</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 text-sm">
              <label>
                <div className="text-slate-700">Username</div>
                <input
                  className="mt-1 w-full border rounded px-3 py-2"
                  value={admin.admin_username}
                  onChange={(e) => setAdmin((s) => ({ ...s, admin_username: e.target.value }))}
                />
              </label>
              <div />
              <label>
                <div className="text-slate-700">Password</div>
                <input
                  className="mt-1 w-full border rounded px-3 py-2"
                  type="password"
                  value={admin.admin_password}
                  onChange={(e) => setAdmin((s) => ({ ...s, admin_password: e.target.value }))}
                />
              </label>
              <label>
                <div className="text-slate-700">Confirm</div>
                <input
                  className="mt-1 w-full border rounded px-3 py-2"
                  type="password"
                  value={admin.confirm}
                  onChange={(e) => setAdmin((s) => ({ ...s, confirm: e.target.value }))}
                />
              </label>

              <div className="md:col-span-2 mt-2 text-xs text-slate-600">
                Submitting will write FreeRADIUS configs and reload the service.
              </div>
            </div>
          </div>
        )}
      </div>

      {err && <div className="mt-4 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded p-3">{err}</div>}

      <div className="mt-4 flex justify-between">
        <button onClick={back} disabled={busy || step === 0} className="px-3 py-2 text-sm rounded border hover:bg-slate-50 disabled:opacity-50">
          Back
        </button>

        {step < 4 ? (
          <button onClick={next} disabled={busy || (step === 1 && includesLdap)} className="px-3 py-2 text-sm rounded bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50">
            Continue
          </button>
        ) : (
          <button onClick={complete} disabled={busy} className="px-3 py-2 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50">
            {busy ? "Completing…" : "Complete setup"}
          </button>
        )}
      </div>
    </div>
  );
}

