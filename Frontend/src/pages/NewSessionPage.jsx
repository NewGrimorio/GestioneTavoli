import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import TextInput from "../components/TextInput.jsx";
import {
  createSession,
  fetchCurrentSession,
  selectCurrentSession,
  selectCurrentSessionStatus,
} from "../features/sessions/sessionsSlice.js";
import { navigate } from "../features/navigation/navigationSlice.js";
import { formatLongDate, todayIso } from "../utils/format.js";

export default function NewSessionPage() {
  const dispatch = useDispatch();
  const current = useSelector(selectCurrentSession);
  const currentStatus = useSelector(selectCurrentSessionStatus);
  const [date, setDate] = useState(todayIso);
  const [nRounds, setNRounds] = useState(3);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (currentStatus === "idle") dispatch(fetchCurrentSession());
  }, [currentStatus, dispatch]);

  const canCreate = date && Number(nRounds) >= 1 && !busy;

  async function handleCreate() {
    setBusy(true);
    setError(null);
    const result = await dispatch(createSession({ nRounds: Number(nRounds), date }));
    if (createSession.fulfilled.match(result)) {
      dispatch(navigate({ name: "players" }));
    } else {
      setError(result.payload ?? result.error.message);
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        title="Nuova Sessione"
        subtitle="I giocatori si aggiungono dopo, dalla sezione Giocatori."
      />

      <div className="mb-7 flex gap-6">
        <label className="flex flex-col gap-1 text-sm text-muted">
          <span>Data</span>
          <TextInput
            type="date"
            value={date}
            className="w-44"
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted">
          <span>Turni</span>
          <TextInput
            type="number"
            min={1}
            max={20}
            value={nRounds}
            className="w-44"
            onChange={(e) => setNRounds(e.target.value)}
          />
        </label>
      </div>

      {current && (
        <Notice kind="warning">
          <span>
            La nuova sessione chiuderà automaticamente quella vecchia (sessione del{" "}
            {formatLongDate(current.date)}).
          </span>
        </Notice>
      )}
      {error && <Notice kind="error">{error}</Notice>}

      <Button variant="primary" onClick={handleCreate} disabled={!canCreate}>
        {busy ? "Creazione…" : "Crea la sessione"}
      </Button>
    </>
  );
}
