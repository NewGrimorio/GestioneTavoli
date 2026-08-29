/**
 * Thin wrapper over fetch for the backend API.
 * Every function returns parsed JSON or throws an Error whose message is
 * readable by the user (the backend's `detail` when available).
 */

const BASE = "/api";

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const response = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, describeError(response.status, body));
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

const post = (path, payload) =>
  request(path, { method: "POST", body: payload === undefined ? undefined : JSON.stringify(payload) });

export const api = {
  listPlayers: () => request("/players"),
  createPlayer: (name) => post("/players", { name }),

  listSessions: () => request("/sessions"),
  getSession: (id) => request(`/sessions/${id}`),
  /** The open session, or null when there is none. */
  getCurrentSession: async () => {
    try {
      return await request("/sessions/current");
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },
  createSession: ({ nRounds, date }) => post("/sessions", { n_rounds: nRounds, date }),
  addParticipant: (sessionId, playerId) =>
    post(`/sessions/${sessionId}/participants`, { player_id: playerId }),
  removeParticipant: (sessionId, playerId) =>
    request(`/sessions/${sessionId}/participants/${playerId}`, { method: "DELETE" }),
  generateTables: (sessionId) => post(`/sessions/${sessionId}/generate`),
  closeSession: (sessionId) => post(`/sessions/${sessionId}/close`),
  deleteSession: (sessionId) => request(`/sessions/${sessionId}`, { method: "DELETE" }),
};
