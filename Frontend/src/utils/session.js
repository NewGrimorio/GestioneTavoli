/** Human label for the state of a session, derived from status + tables. */
export function sessionStage(session) {
  if (session.status === "closed") return "closed";
  return session.tables_generated ? "playing" : "preparing";
}

export const STAGE_LABELS = {
  preparing: "In preparazione",
  playing: "In corso",
  closed: "Chiusa",
};
