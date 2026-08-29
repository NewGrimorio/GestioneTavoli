import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import ScheduleGrid from "../components/ScheduleGrid.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import {
  closeSession,
  deleteSession,
  fetchSession,
  selectSessionDetail,
  selectSessionDetailStatus,
  selectSessionsError,
} from "../features/sessions/sessionsSlice.js";
import { navigate } from "../features/navigation/navigationSlice.js";
import { formatLongDate, pluralize } from "../utils/format.js";

export default function SessionDetailPage({ id }) {
  const dispatch = useDispatch();
  const session = useSelector(selectSessionDetail);
  const status = useSelector(selectSessionDetailStatus);
  const loadError = useSelector(selectSessionsError);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (session?.id !== id) dispatch(fetchSession(id));
  }, [id, session?.id, dispatch]);

  async function run(thunk, { confirm, then }) {
    if (confirm && !window.confirm(confirm)) return;
    setBusy(true);
    setError(null);
    const result = await dispatch(thunk);
    if (result.meta.requestStatus === "fulfilled") {
      if (then) then();
    } else {
      setError(result.payload ?? result.error.message);
    }
    setBusy(false);
  }

  if (status === "failed") return <Notice kind="error">{loadError}</Notice>;
  if (!session || session.id !== id) return <Notice>Caricamento…</Notice>;

  const isOpen = session.status === "open";

  return (
    <>
      <PageHead
        title={
          <span className="flex items-center gap-3">
            {formatLongDate(session.date)}
            <StatusBadge session={session} />
          </span>
        }
        subtitle={[
          pluralize(session.participants.length, "giocatore", "giocatori"),
          pluralize(session.n_rounds, "turno", "turni"),
          session.seed !== null && `seme ${session.seed}`,
        ]
          .filter(Boolean)
          .join(" · ")}
        actions={
          <div className="print-hidden flex gap-2">
            {isOpen && (
              <Button
                disabled={busy}
                onClick={() =>
                  run(closeSession(session.id), {
                    confirm: "Chiudere questa sessione? Non sarà più possibile modificarla.",
                  })
                }
              >
                Chiudi sessione
              </Button>
            )}
            <Button
              variant="danger"
              disabled={busy}
              onClick={() =>
                run(deleteSession(session.id), {
                  confirm: "Eliminare questa sessione? Iscritti e tavoli andranno persi.",
                  then: () => dispatch(navigate({ name: "sessions" })),
                })
              }
            >
              Elimina sessione
            </Button>
          </div>
        }
      />

      {error && <Notice kind="error">{error}</Notice>}

      {session.tables_generated ? (
        <ScheduleGrid rounds={session.rounds} />
      ) : (
        <Notice>
          <span>Tavoli non ancora generati.</span>
          {isOpen && (
            <Button onClick={() => dispatch(navigate({ name: "players" }))}>
              Vai ai giocatori
            </Button>
          )}
        </Notice>
      )}
    </>
  );
}
