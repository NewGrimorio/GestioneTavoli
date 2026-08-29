import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
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
  const [pending, setPending] = useState(null); // null | "close" | "delete"

  useEffect(() => {
    if (session?.id !== id) dispatch(fetchSession(id));
  }, [id, session?.id, dispatch]);

  async function confirmPending() {
    setBusy(true);
    setError(null);
    const isDelete = pending === "delete";
    const result = await dispatch(isDelete ? deleteSession(id) : closeSession(id));
    if (result.meta.requestStatus === "fulfilled") {
      if (isDelete) dispatch(navigate({ name: "sessions" }));
    } else {
      setError(result.payload ?? result.error.message);
    }
    setBusy(false);
    setPending(null);
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
              <Button variant="amber" disabled={busy} onClick={() => setPending("close")}>
                Chiudi sessione
              </Button>
            )}
            <Button variant="danger" disabled={busy} onClick={() => setPending("delete")}>
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

      <ConfirmDialog
        open={pending === "close"}
        title="Chiudere la sessione?"
        confirmLabel="Chiudi sessione"
        tone="amber"
        busy={busy}
        onConfirm={confirmPending}
        onCancel={() => setPending(null)}
      >
        La sessione del {formatLongDate(session.date)} verrà chiusa e non sarà più possibile
        modificarla. Resterà consultabile nell'elenco.
      </ConfirmDialog>

      <ConfirmDialog
        open={pending === "delete"}
        title="Eliminare la sessione?"
        confirmLabel="Elimina sessione"
        tone="danger"
        busy={busy}
        onConfirm={confirmPending}
        onCancel={() => setPending(null)}
      >
        La sessione del {formatLongDate(session.date)} verrà eliminata con iscritti e tavoli.
        L'operazione non si può annullare.
      </ConfirmDialog>
    </>
  );
}
