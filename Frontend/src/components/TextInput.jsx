export default function TextInput({ className = "", ...props }) {
  return (
    <input
      className={`rounded-md border border-line bg-white px-2.5 py-2 text-ink focus-visible:outline-2 focus-visible:outline-felt focus-visible:outline-offset-2 ${className}`}
      {...props}
    />
  );
}
