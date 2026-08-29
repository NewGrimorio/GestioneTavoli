import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import {
  fetchSessions,
  selectSessions,
  selectSessionsError,
  selectSessionsStatus,
} from "../features/sessions/sessionsSlice.js";
import { navigate } from "../features/navigation/navigationSlice.js";
import { formatLongDate, pluralize } from "../utils/format.js";

export default function SessionsPage() {
  const dispatch = useDispatch();
  const sessions = useSelector(selectSessions);
  const status = useSelector(selectSessionsStatus);
  const error = useSelector(selectSessionsError);

  useEffect(() => {
    if (status === "idle") dispatch(fetchSessions());
  }, [status, dispatch]);

  return (
    <>
      <PageHead
        title="Elenco Sessioni"
        actions={
          <Button variant="primary" onClick={() => dispatch(navigate({ name: "new-session" }))}>
            Nuova sessione
          </Button>
        }
      />

      {status === "failed" && (
        <Notice kind="error">Impossibile caricare le sessioni: {error}</Notice>
      )}
      {status === "succeeded" && sessions.length === 0 && (
        <Notice>Nessuna sessione ancora. Crea la prima con «Nuova sessione».</Notice>
      )}
      {sessions.length > 0 && (
        <ul className="flex max-w-2xl flex-col gap-2">
          {sessions.map((session) => (
            <li key={session.id}>
              <button
                type="button"
                onClick={() => dispatch(navigate({ name: "session", id: session.id }))}
                className="flex w-full flex-col gap-1 rounded-md border border-line bg-white px-4 py-3.5 text-left cursor-pointer hover:border-ink focus-visible:outline-2 focus-visible:outline-felt sm:flex-row sm:items-center sm:justify-between sm:gap-4"
              >
                <span className="flex items-center gap-3">
                  <span className="font-display text-[19px] capitalize">
                    {formatLongDate(session.date)}
                  </span>
                  <StatusBadge session={session} />
                </span>
                <span className="text-sm text-muted">
                  {pluralize(session.n_participants, "giocatore", "giocatori")} ·{" "}
                  {pluralize(session.n_rounds, "turno", "turni")}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
