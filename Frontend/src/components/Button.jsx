const VARIANTS = {
  default: "border-ink bg-white text-ink hover:bg-paper",
  primary: "border-felt bg-felt text-white hover:bg-felt-dark",
  danger: "border-danger bg-white text-danger hover:bg-red-50",
  quiet: "border-transparent bg-transparent text-muted hover:text-ink px-2 py-1",
};

export default function Button({ variant = "default", className = "", ...props }) {
  return (
    <button
      type="button"
      className={`rounded-md border px-3.5 py-2 whitespace-nowrap cursor-pointer disabled:opacity-45 disabled:cursor-default disabled:hover:bg-inherit focus-visible:outline-2 focus-visible:outline-felt focus-visible:outline-offset-2 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
