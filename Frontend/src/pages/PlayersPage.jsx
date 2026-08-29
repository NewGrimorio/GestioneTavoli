import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import Button from "../components/Button.jsx";
import Notice from "../components/Notice.jsx";
import PageHead from "../components/PageHead.jsx";
import TextInput from "../components/TextInput.jsx";
import {
  addPlayer,
  fetchPlayers,
  selectPlayers,
  selectPlayersError,
  selectPlayersStatus,
} from "../features/players/playersSlice.js";

export default function PlayersPage() {
  const dispatch = useDispatch();
  const players = useSelector(selectPlayers);
  const status = useSelector(selectPlayersStatus);
  const loadError = useSelector(selectPlayersError);
  const [name, setName] = useState("");
  const [addError, setAddError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (status === "idle") dispatch(fetchPlayers());
  }, [status, dispatch]);

  async function handleAdd() {
    const clean = name.trim();
    if (!clean) return;
    setSaving(true);
    setAddError(null);
    const result = await dispatch(addPlayer(clean));
    if (addPlayer.fulfilled.match(result)) {
      setName("");
    } else {
      setAddError(result.payload ?? result.error.message);
    }
    setSaving(false);
  }

  return (
    <>
      <PageHead title="Giocatori" />

      <div className="mb-4 flex max-w-lg gap-2">
        <TextInput
          type="text"
          value={name}
          placeholder="Nome e cognome, oppure username"
          aria-label="Nome del nuovo giocatore"
          maxLength={80}
          className="flex-1"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        />
        <Button variant="primary" onClick={handleAdd} disabled={saving || !name.trim()}>
          Aggiungi
        </Button>
      </div>

      {addError && <Notice kind="error">{addError}</Notice>}
      {status === "failed" && <Notice kind="error">{loadError}</Notice>}
      {status === "succeeded" && players.length === 0 && (
        <Notice>Nessun giocatore registrato. Aggiungi il primo qui sopra.</Notice>
      )}
      {players.length > 0 && (
        <ul className="max-w-4xl columns-[220px] gap-8">
          {players.map((player) => (
            <li key={player.id} className="break-inside-avoid border-b border-line py-1.5">
              {player.name}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
