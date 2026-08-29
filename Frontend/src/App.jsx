import { useDispatch, useSelector } from "react-redux";
import { navigate, selectView } from "./features/navigation/navigationSlice.js";
import SessionDetailPage from "./pages/SessionDetailPage.jsx";
import SessionsPage from "./pages/SessionsPage.jsx";
import NewSessionPage from "./pages/NewSessionPage.jsx";
import PlayersPage from "./pages/PlayersPage.jsx";

const SECTIONS = [
  { name: "sessions", label: "Elenco Sessioni" },
  { name: "new-session", label: "Nuova Sessione" },
  { name: "players", label: "Giocatori" },
];

export default function App() {
  const dispatch = useDispatch();
  const view = useSelector(selectView);
  const section = view.name === "session" ? "sessions" : view.name;

  return (
    <div className="min-h-screen">
      <header className="print-hidden flex flex-col gap-3 border-b-2 border-ink bg-white px-4 py-3.5 sm:flex-row sm:items-baseline sm:gap-8 sm:px-8 sm:py-4">
        <h1 className="font-display text-[22px] font-medium">Gestione Tavoli</h1>
        <nav className="flex gap-1" aria-label="Sezioni">
          {SECTIONS.map(({ name, label }) => {
            const active = section === name;
            return (
              <button
                key={name}
                type="button"
                aria-current={active ? "page" : undefined}
                onClick={() => dispatch(navigate({ name }))}
                className={`rounded-md px-3 py-1.5 cursor-pointer focus-visible:outline-2 focus-visible:outline-cardback ${
                  active ? "bg-ink text-white" : "text-muted hover:text-ink"
                }`}
              >
                {label}
              </button>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-[1400px] px-4 pt-5 pb-12 sm:px-8 sm:pt-7 sm:pb-16">
        {view.name === "sessions" && <SessionsPage />}
        {view.name === "new-session" && <NewSessionPage />}
        {view.name === "players" && <PlayersPage />}
        {view.name === "session" && <SessionDetailPage id={view.id} />}
      </main>
    </div>
  );
}
