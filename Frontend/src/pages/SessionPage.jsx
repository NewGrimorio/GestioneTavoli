import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import ScheduleGrid from "../components/ScheduleGrid.jsx";
import {
  deleteSession,
  fetchSession,
  selectCurrentSession,
  selectCurrentSessionStatus,
  selectSessionsError,
} from "../features/sessions/sessionsSlice.js";
import { navigate } from "../features/navigation/navigationSlice.js";
import { formatLongDate, pluralize } from "../utils/format.js";

export default function SessionPage({ id }) {
  const dispatch = useDispatch();
  const session = useSelector(selectCurrentSession);
  const status = useSelector(selectCurrentSessionStatus);
  const error = useSelector(selectSessionsError);
  const [deleteError, setDeleteError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (session?.id !== id) dispatch(fetchSession(id));
  }, [id, session?.id, dispatch]);

  async function handleDelete() {
    if (!window.confirm("Eliminare questa sessione? I tavoli generati andranno persi.")) return;
    setDeleting(true);
    const result = await dispatch(deleteSession(id));
    if (deleteSession.fulfilled.match(result)) {
      dispatch(navigate({ name: "sessions" }));
    } else {
      setDeleteError(result.payload ?? result.error.message);
      setDeleting(false);
    }
  }

  if (status === "failed") return <Notice kind="error">{error}</Notice>;
  if (!session || session.id !== id) return <Notice>Caricamento…</Notice>;

  const nPlayers = session.rounds[0].tables.reduce((n, t) => n + t.players.length, 0);

  return (
    <>
      <PageHead
        title={formatLongDate(session.date)}
        subtitle={`${pluralize(nPlayers, "giocatore", "giocatori")} · ${pluralize(
          session.n_rounds,
          "turno",
          "turni",
        )} · seme ${session.seed}`}
        actions={
          <Button
            variant="danger"
            className="print-hidden"
            onClick={handleDelete}
            disabled={deleting}
          >
            Elimina sessione
          </Button>
        }
      />
      {deleteError && <Notice kind="error">{deleteError}</Notice>}
      <ScheduleGrid rounds={session.rounds} />
    </>
  );
}
