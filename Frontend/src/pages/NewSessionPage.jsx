import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import TextInput from "../components/TextInput.jsx";
import { createSession } from "../features/sessions/sessionsSlice.js";
import { navigate } from "../features/navigation/navigationSlice.js";
import {
  addPlayer,
  fetchPlayers,
  selectPlayers,
  selectPlayersStatus,
} from "../features/players/playersSlice.js";
import { todayIso } from "../utils/format.js";
import { MIN_PLAYERS, describeTables, tableSizes } from "../utils/tables.js";

export default function NewSessionPage() {
  const dispatch = useDispatch();
  const players = useSelector(selectPlayers);
  const playersStatus = useSelector(selectPlayersStatus);
  const [selected, setSelected] = useState(() => new Set());
  const [date, setDate] = useState(todayIso);
  const [nRounds, setNRounds] = useState(3);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (playersStatus === "idle") dispatch(fetchPlayers());
  }, [playersStatus, dispatch]);

  const sizes = useMemo(() => tableSizes(selected.size), [selected.size]);
  const canCreate = selected.size >= MIN_PLAYERS && Number(nRounds) >= 1 && !busy;

  function toggle(id) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleAddPlayer() {
    const clean = newName.trim();
    if (!clean) return;
    setError(null);
    const result = await dispatch(addPlayer(clean));
    if (addPlayer.fulfilled.match(result)) {
      setSelected((current) => new Set(current).add(result.payload.id));
      setNewName("");
    } else {
      setError(result.payload ?? result.error.message);
    }
  }

  async function handleCreate() {
    setBusy(true);
    setError(null);
    const result = await dispatch(
      createSession({ playerIds: [...selected], nRounds: Number(nRounds), date }),
    );
    if (createSession.fulfilled.match(result)) {
      dispatch(navigate({ name: "session", id: result.payload.id }));
    } else {
      setError(result.payload ?? result.error.message);
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead title="Nuova Sessione" />

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

      <section className="mb-6" aria-labelledby="picker-title">
        <div className="mb-2 flex items-baseline justify-between">
          <h3 id="picker-title" className="text-lg font-semibold">
            Chi partecipa
          </h3>
          {players.length > 0 && (
            <div className="flex gap-1">
              <Button
                variant="quiet"
                onClick={() => setSelected(new Set(players.map((p) => p.id)))}
              >
                Tutti
              </Button>
              <Button variant="quiet" onClick={() => setSelected(new Set())}>
                Nessuno
              </Button>
            </div>
          )}
        </div>

        {playersStatus === "succeeded" && players.length === 0 && (
          <Notice>Nessun giocatore registrato: aggiungine qui sotto.</Notice>
        )}
        {players.length > 0 && (
          <ul className="mb-4 columns-[200px] gap-6">
            {players.map((player) => (
              <li key={player.id} className="break-inside-avoid">
                <label className="flex cursor-pointer items-center gap-2 py-1.5">
                  <input
                    type="checkbox"
                    className="size-[18px] accent-felt"
                    checked={selected.has(player.id)}
                    onChange={() => toggle(player.id)}
                  />
                  <span>{player.name}</span>
                </label>
              </li>
            ))}
          </ul>
        )}

        <div className="flex max-w-lg gap-2">
          <TextInput
            type="text"
            value={newName}
            placeholder="Nuovo giocatore"
            aria-label="Nome del nuovo giocatore"
            maxLength={80}
            className="flex-1"
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddPlayer()}
          />
          <Button onClick={handleAddPlayer} disabled={!newName.trim()}>
            Aggiungi e seleziona
          </Button>
        </div>
      </section>

      {error && <Notice kind="error">{error}</Notice>}

      <div className="sticky bottom-0 flex items-center justify-between gap-4 rounded-md border border-ink bg-white px-4 py-3.5">
        <p>
          {selected.size < MIN_PLAYERS
            ? `${selected.size} selezionati · ne servono almeno ${MIN_PLAYERS}`
            : `${selected.size} selezionati · ${describeTables(sizes)}`}
        </p>
        <Button variant="primary" onClick={handleCreate} disabled={!canCreate}>
          {busy ? "Creazione…" : "Crea la sessione"}
        </Button>
      </div>
    </>
  );
}
