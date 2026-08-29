/**
 * Thin wrapper over fetch for the backend API.
 * Every function returns parsed JSON or throws an Error whose message is
 * readable by the user (the backend's `detail` when available).
 */

const BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(describeError(response.status, body));
  }
  return body;
}

function describeError(status, body) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg).join("; ");
  }
  return `Errore ${status}`;
}

export const api = {
  listPlayers: () => request("/players"),
  createPlayer: (name) =>
    request("/players", { method: "POST", body: JSON.stringify({ name }) }),

  // Backend routes keep their original name.
  listSessions: () => request("/evenings"),
  getSession: (id) => request(`/evenings/${id}`),
  createSession: ({ playerIds, nRounds, date }) =>
    request("/evenings", {
      method: "POST",
      body: JSON.stringify({ player_ids: playerIds, n_rounds: nRounds, date }),
    }),
  deleteSession: (id) => request(`/evenings/${id}`, { method: "DELETE" }),
};
