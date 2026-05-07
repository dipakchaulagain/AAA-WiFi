import React from "react";
import { logStreamUrl, testAuth, testLdap } from "../api/diagnostics";

function colorLine(line: string) {
  if (line.includes("Access-Accept")) return "text-emerald-300";
  if (line.includes("Access-Reject")) return "text-rose-300";
  if (line.includes("Access-Challenge")) return "text-amber-300";
  return "text-slate-200";
}

export default function Diagnostics() {
  const [auth, setAuth] = React.useState({ username: "", password: "" });
  const [authOut, setAuthOut] = React.useState<string>("");
  const [authOk, setAuthOk] = React.useState<boolean | null>(null);

  const [ldapRes, setLdapRes] = React.useState<any>(null);

  const [lines, setLines] = React.useState<string[]>([]);
  const boxRef = React.useRef<HTMLDivElement | null>(null);

  async function runAuth() {
    const r = await testAuth(auth.username, auth.password);
    setAuthOk(r.success);
    setAuthOut(r.output);
  }

  async function runLdap() {
    setLdapRes(await testLdap());
  }

  React.useEffect(() => {
    const es = new EventSource(logStreamUrl(), { withCredentials: true } as any);
    es.onmessage = (ev) => {
      setLines((prev) => {
        const next = [...prev, ev.data];
        return next.slice(-400);
      });
    };
    return () => es.close();
  }, []);

  React.useEffect(() => {
    if (!boxRef.current) return;
    boxRef.current.scrollTop = boxRef.current.scrollHeight;
  }, [lines.length]);

  return (
    <div className="space-y-6">
      <div className="bg-white border rounded p-4">
        <div className="font-medium">Test authentication</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-3 text-sm">
          <input className="border rounded px-2 py-1.5" placeholder="username" value={auth.username} onChange={(e) => setAuth((s) => ({ ...s, username: e.target.value }))} />
          <input className="border rounded px-2 py-1.5" placeholder="password" type="password" value={auth.password} onChange={(e) => setAuth((s) => ({ ...s, password: e.target.value }))} />
          <button onClick={runAuth} className="px-3 py-1.5 rounded bg-slate-900 text-white hover:bg-slate-800">
            Test
          </button>
        </div>
        {authOk != null && (
          <div className={`mt-3 text-sm ${authOk ? "text-emerald-700" : "text-rose-700"}`}>
            {authOk ? "PASS" : "FAIL"}
          </div>
        )}
        {authOut && (
          <pre className="mt-2 text-xs bg-slate-950 text-slate-100 rounded p-3 overflow-x-auto whitespace-pre-wrap">
            {authOut}
          </pre>
        )}
      </div>

      <div className="bg-white border rounded p-4">
        <div className="font-medium">Test LDAP</div>
        <button onClick={runLdap} className="mt-3 px-3 py-1.5 rounded border hover:bg-slate-50 text-sm">
          Run test
        </button>
        {ldapRes && (
          <pre className="mt-3 text-xs bg-slate-50 border rounded p-3 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(ldapRes, null, 2)}
          </pre>
        )}
      </div>

      <div className="bg-white border rounded p-4">
        <div className="font-medium">Live FreeRADIUS log</div>
        <div
          ref={boxRef}
          className="mt-3 h-80 overflow-auto bg-slate-950 rounded p-3 font-mono text-xs"
        >
          {lines.map((l, i) => (
            <div key={i} className={colorLine(l)}>
              {l}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

