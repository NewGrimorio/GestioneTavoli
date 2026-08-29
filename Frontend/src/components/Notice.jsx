/** Inline message for errors, warnings, empty states and confirmations. */
const TONES = {
  info: "border-line bg-white text-ink",
  warning: "border-amber-400 bg-amber-50 text-amber-900",
  error: "border-danger bg-white text-danger",
};

export default function Notice({ kind = "info", children }) {
  return (
    <div
      className={`mb-4 flex flex-col gap-3 rounded-md border px-3.5 py-2.5 sm:flex-row sm:items-center sm:justify-between ${TONES[kind]}`}
      role={kind === "error" ? "alert" : "status"}
    >
      {children}
    </div>
  );
}
