import React from "react";

export default function ConfirmDialog({
  title,
  message,
  confirmText = "Confirm",
  open,
  onCancel,
  onConfirm,
}: {
  title: string;
  message: string;
  confirmText?: string;
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/40 grid place-items-center p-4">
      <div className="bg-white rounded shadow max-w-md w-full p-4">
        <div className="font-semibold">{title}</div>
        <div className="text-sm text-slate-600 mt-2">{message}</div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onCancel} className="px-3 py-1.5 text-sm rounded border hover:bg-slate-50">
            Cancel
          </button>
          <button onClick={onConfirm} className="px-3 py-1.5 text-sm rounded bg-slate-900 text-white hover:bg-slate-800">
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

