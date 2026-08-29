// Each variant carries its own shape and padding so classes never compete.
const VARIANTS = {
  default: "rounded-md border-ink bg-white px-3.5 py-2 text-ink hover:bg-paper",
  primary: "rounded-md border-cardback bg-cardback px-3.5 py-2 text-white hover:bg-cardback-dark",
  amber: "rounded-md border-amber-600 bg-amber-600 px-3.5 py-2 text-white hover:bg-amber-700",
  danger: "rounded-md border-danger bg-danger px-3.5 py-2 text-white hover:bg-red-900",
  quiet: "rounded-md border-transparent bg-transparent px-2 py-1 text-muted hover:text-ink",
  // Small filled pill in light red, for "remove from list" actions.
  remove:
    "rounded-full border-red-200 bg-red-200 px-3 py-1 text-sm font-medium text-red-900 hover:bg-red-300",
};

export default function Button({ variant = "default", className = "", ref, ...props }) {
  return (
    <button
      ref={ref}
      type="button"
      className={`border whitespace-nowrap cursor-pointer disabled:opacity-45 disabled:cursor-default focus-visible:outline-2 focus-visible:outline-cardback focus-visible:outline-offset-2 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
