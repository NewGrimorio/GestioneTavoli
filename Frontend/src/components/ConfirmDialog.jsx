import { useEffect, useRef } from "react";
import Button from "./Button.jsx";

/**
 * Modal confirmation, replacing window.confirm. Rendered only while `open`.
 * `tone` picks the confirm button: "primary" (brown) or "danger" (red).
 */
export default function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel = "Conferma",
  cancelLabel = "Annulla",
  tone = "primary",
  busy = false,
  onConfirm,
  onCancel,
}) {
  const confirmRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    confirmRef.current?.focus();
    const onKey = (e) => e.key === "Escape" && !busy && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 p-4"
      onClick={() => !busy && onCancel()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="w-full max-w-lg rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="confirm-title" className="border-b border-line px-6 py-4 text-xl font-semibold">
          {title}
        </h2>
        <div className="px-6 py-5 text-muted">{children}</div>
        <div className="flex justify-end gap-2 px-6 pb-5">
          <Button variant="quiet" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </Button>
          <Button ref={confirmRef} variant={tone} onClick={onConfirm} disabled={busy}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
