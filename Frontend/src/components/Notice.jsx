/** Inline message for errors, empty states and confirmations. */
export default function Notice({ kind = "info", children }) {
  const tone =
    kind === "error" ? "border-danger text-danger" : "border-line text-ink";
  return (
    <p
      className={`mb-4 rounded-md border bg-white px-3.5 py-2.5 ${tone}`}
      role={kind === "error" ? "alert" : "status"}
    >
      {children}
    </p>
  );
}
