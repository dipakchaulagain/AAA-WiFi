import React from "react";

export default function StatusBadge({ ok, text }: { ok: boolean; text: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
      }`}
    >
      {text}
    </span>
  );
}

