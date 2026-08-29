import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import TextInput from "../components/TextInput.jsx";
import { navigate } from "../features/navigation/navigationSlice.js";
import {
  addPlayer,
  fetchPlayers,
  selectPlayers,
  selectPlayersError,
  selectPlayersStatus,
} from "../features/players/playersSlice.js";
import {
  addParticipant,
  fetchCurrentSession,
  generateTables,
  removeParticipant,
  selectCurrentSession,
  selectCurrentSessionStatus,
  selectSessionsError,
} from "../features/sessions/sessionsSlice.js";
import { formatLongDate, pluralize } from "../utils/format.js";
import { MIN_PLAYERS, describeTables, tableSizes } from "../utils/tables.js";

export default function PlayersPage() {
  const dispatch = useDispatch();
  const session = useSelector(selectCurrentSession);
  const sessionStatus = useSelector(selectCurrentSessionStatus);
  const sessionError = useSelector(selectSessionsError);

  useEffect(() => {
    if (sessionStatus === "idle") dispatch(fetchCurrentSession());
  }, [sessionStatus, dispatch]);

  if (sessionStatus === "failed") return <Notice kind="error">{sessionError}</Notice>;
  if (sessionStatus !== "succeeded") return <Notice>Caricamento…</Notice>;

  if (!session) {
    return (
      <>
        <PageHead title="Giocatori" />
        <Notice>
          <span>Nessuna sessione attiva. Per aggiungere giocatori serve una sessione aperta.</span>
          <Button variant="primary" onClick={() => dispatch(navigate({ name: "new-session" }))}>
            Nuova sessione
          </Button>
        </Notice>
      </>
    );
  }

  if (session.tables_generated) {
    return (
      <>
        <PageHead
          title="Giocatori"
          subtitle={`Sessione del ${formatLongDate(session.date)} · ${pluralize(
            session.participants.length,
            "iscritto",
            "iscritti",
          )}`}
        />
        <Notice>
          <span>
            I tavoli sono già generati. Per aggiungere un ritardatario va creata una nuova
            sessione.
          </span>
          <Button onClick={() => dispatch(navigate({ name: "session", id: session.id }))}>
            Vedi i tavoli
          </Button>
        </Notice>
        <ParticipantList participants={session.participants} />
      </>
    );
  }

  return <SignUp session={session} />;
}

/** Sign-up view: registry on the left, participants on the right, generate at the bottom. */
function SignUp({ session }) {
  const dispatch = useDispatch();
  const players = useSelector(selectPlayers);
  const playersStatus = useSelector(selectPlayersStatus);
  const playersError = useSelector(selectPlayersError);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (playersStatus === "idle") dispatch(fetchPlayers());
  }, [playersStatus, dispatch]);

  const signedIds = useMemo(
    () => new Set(session.participants.map((p) => p.id)),
    [session.participants],
  );
  const available = players.filter((p) => !signedIds.has(p.id));
  const sizes = tableSizes(session.participants.length);
  const canGenerate = session.participants.length >= MIN_PLAYERS && !busy;

  async function signUp(playerId) {
    setError(null);
    const result = await dispatch(addParticipant({ sessionId: session.id, playerId }));
    if (!addParticipant.fulfilled.match(result)) {
      setError(result.payload ?? result.error.message);
    }
  }

  async function handleRemove(playerId) {
    setError(null);
    const result = await dispatch(removeParticipant({ sessionId: session.id, playerId }));
    if (!removeParticipant.fulfilled.match(result)) {
      setError(result.payload ?? result.error.message);
    }
  }

  async function handleAddNew() {
    const clean = newName.trim();
    if (!clean) return;
    setError(null);
    const result = await dispatch(addPlayer(clean));
    if (addPlayer.fulfilled.match(result)) {
      setNewName("");
      await signUp(result.payload.id);
    } else {
      setError(result.payload ?? result.error.message);
    }
  }

  async function handleGenerate() {
    setBusy(true);
    setError(null);
    const result = await dispatch(generateTables(session.id));
    if (generateTables.fulfilled.match(result)) {
      dispatch(navigate({ name: "session", id: session.id }));
    } else {
      setError(result.payload ?? result.error.message);
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        title="Giocatori"
        subtitle={`Vuoi aggiungere giocatori alla sessione del ${formatLongDate(session.date)}?`}
      />

      {error && <Notice kind="error">{error}</Notice>}
      {playersStatus === "failed" && <Notice kind="error">{playersError}</Notice>}

      <div className="mb-6 grid gap-8 md:grid-cols-2">
        <section aria-labelledby="registry-title">
          <h3 id="registry-title" className="mb-2 text-lg font-semibold">
            Anagrafica
          </h3>
          <div className="mb-3 flex gap-2">
            <TextInput
              type="text"
              value={newName}
              placeholder="Nome nuovo giocatore"
              aria-label="Nome del nuovo giocatore"
              maxLength={80}
              className="flex-1"
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddNew()}
            />
            <Button onClick={handleAddNew} disabled={!newName.trim()}>
              Aggiungi e iscrivi
            </Button>
          </div>
          {playersStatus === "succeeded" && available.length === 0 && (
            <p className="text-sm text-muted">
              {players.length === 0
                ? "Nessun nome in anagrafica: scrivi il primo qui sopra."
                : "Tutti i nomi in anagrafica sono già iscritti."}
            </p>
          )}
          {available.length > 0 && (
            <ul className="grid rounded-md border border-line bg-white sm:grid-cols-2">
              {available.map((player) => (
                <li
                  key={player.id}
                  className="flex items-center justify-between border-b border-line px-3 py-1.5"
                >
                  <span>{player.name}</span>
                  <Button variant="quiet" onClick={() => signUp(player.id)}>
                    Iscrivi
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="participants-title">
          <h3 id="participants-title" className="mb-2 text-lg font-semibold">
            Iscritti ({session.participants.length})
          </h3>
          {session.participants.length === 0 ? (
            <p className="text-sm text-muted">Nessun iscritto: scegli dall'anagrafica o aggiungi un nome.</p>
          ) : (
            <ParticipantList participants={session.participants} onRemove={handleRemove} />
          )}
        </section>
      </div>

      <div className="sticky bottom-0 flex items-center justify-between gap-4 rounded-md border border-ink bg-white px-4 py-3.5">
        <p>
          {session.participants.length < MIN_PLAYERS
            ? `${session.participants.length} iscritti · ne servono almeno ${MIN_PLAYERS}`
            : `${session.participants.length} iscritti · ${describeTables(sizes)}`}
        </p>
        <Button variant="primary" onClick={handleGenerate} disabled={!canGenerate}>
          {busy ? "Generazione…" : "Genera tavoli"}
        </Button>
      </div>
    </>
  );
}

function ParticipantList({ participants, onRemove }) {
  return (
    <ul className="grid rounded-md border border-line bg-white sm:grid-cols-2">
      {participants.map((player) => (
        <li
          key={player.id}
          className="flex items-center justify-between border-b border-line px-3 py-1.5"
        >
          <span>{player.name}</span>
          {onRemove && (
            <Button
              variant="remove"
              aria-label={`Togli ${player.name}`}
              onClick={() => onRemove(player.id)}
            >
              Togli
            </Button>
          )}
        </li>
      ))}
    </ul>
  );
}
