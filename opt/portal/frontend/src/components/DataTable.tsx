import React from "react";

export type Column<T> = {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
};

export default function DataTable<T extends { [k: string]: any }>({
  columns,
  rows,
  emptyText = "No data",
}: {
  columns: Column<T>[];
  rows: T[];
  emptyText?: string;
}) {
  return (
    <div className="border rounded bg-white overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((c) => (
              <th key={c.key} className="text-left font-medium text-slate-700 px-3 py-2">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="px-3 py-6 text-slate-500" colSpan={columns.length}>
                {emptyText}
              </td>
            </tr>
          ) : (
            rows.map((r, idx) => (
              <tr key={idx} className="border-t">
                {columns.map((c) => (
                  <td key={c.key} className="px-3 py-2 text-slate-800">
                    {c.render ? c.render(r) : String(r[c.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

