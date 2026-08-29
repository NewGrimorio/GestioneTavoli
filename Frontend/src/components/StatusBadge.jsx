import { STAGE_LABELS, sessionStage } from "../utils/session.js";

const TONES = {
  preparing: "bg-amber-100 text-amber-900 border-amber-300",
  playing: "bg-green-100 text-green-900 border-green-300",
  closed: "bg-paper text-muted border-line",
};

export default function StatusBadge({ session }) {
  const stage = sessionStage(session);
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${TONES[stage]}`}
    >
      {STAGE_LABELS[stage]}
    </span>
  );
}
