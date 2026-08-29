# Decisioni architetturali

Registro delle scelte prese durante lo sviluppo. Ogni voce: data, decisione, motivazione.

## 2026-08-29 — Stack backend

- Python 3.12, FastAPI, SQLite tramite SQLAlchemy 2.0, pytest.
- Nessun servizio esterno: l'app va impacchettata come desktop, SQLite in un file locale rende il packaging banale.
- FastAPI e SQLAlchemy vengono aggiunti solo quando servono (API e persistenza); il primo passo è puro dominio.

## 2026-08-29 — Struttura repository

Cartelle di primo livello: `Backend/`, `Frontend/`, `docs/` (maiuscole come scelte dall'autore).

```
Backend/app/domain/    logica pura, zero import da FastAPI o DB, testata con pytest
Backend/app/models/    entità SQLAlchemy
Backend/app/services/  orchestrazione dominio + DB (``*_service.py``)
Backend/app/routers/   solo I/O HTTP, nessuna logica di business (``*_router.py``); dipendenza DB ``get_db``
Backend/app/schemas.py Pydantic: forme JSON scambiate col frontend
Backend/app/main.py    application factory ``create_app``
Backend/app/db.py      engine, session factory, percorso del file SQLite
Backend/tests/         pytest; DB in memoria tramite fixture ``session``
```

## 2026-08-29 — Composizione tavoli

- Regola: massimo numero di tavoli da 4, resto in tavoli da 3 (`n = 4a + 3b` con `b` minimo). Tavoli da 4 prima, da 3 dopo.
- Minimo 6 giocatori (due tavoli). Sotto si solleva `ValueError`; `n = 5` non è comunque rappresentabile.
- Confermato dalla serata di riferimento: 22 giocatori → 4 tavoli da 4 + 2 da 3.

## 2026-08-29 — Turni della serata libera

- Numero di turni scelto dall'utente (parametro, non costante).
- Unico obiettivo: minimizzare gli incontri ripetuti tra coppie di giocatori. Nessun vincolo "coppie fisse" (la ripetizione Angelo/Emanuele nell'Excel era casuale).
- Nessuna regola di rotazione tra tavoli da 3 e da 4: chi finisce ai tavoli da 3 è casuale. Da riconsiderare se in pratica risulta sbilanciato.
- Algoritmo: turno per turno, iterated local search (deal casuale → scambi migliorativi tra tavoli → kick casuale → nuova discesa), 30 restart per turno. Costo di un incontro = (incontri precedenti)², così le ripetizioni inevitabili si spalmano invece di concentrarsi su poche coppie.
- Output riproducibile dato un `seed`: servirà per rigenerare la stessa serata e per i test.
- Limiti noti: con pochi giocatori e molti turni le ripetizioni sono inevitabili per costruzione (12 giocatori × 3 turni: minimo teorico 6, l'algoritmo trova 9). Tempi: millisecondi nei casi reali, ~1 s nei casi patologici.

## 2026-08-29 — Modello dati

- Terminologia: **sessione** (`Session`) è la serata di gioco; il nome `Evening` usato all'inizio è stato sostituito ovunque (modello, service, router, API `/api/sessions`).
- `Player(id, name)`: `name` unico, etichetta libera (nome e cognome, oppure username). Nessuna separazione nome/cognome.
- `Session(id, date, kind, status, n_rounds, seed)`: `kind` è `free` o `ranked` fin da subito, anche se ora esiste solo la sessione libera. `status` è `open` o `closed`. Il `seed` è `None` finché i tavoli non sono generati, poi sempre valorizzato (estratto a caso se non fornito) così la sessione è rigenerabile.
- `Participant(session_id, player_id)`: chi è iscritto alla sessione, compilato prima della generazione dei tavoli.
- `Round(session_id, number)` → `GameTable(round_id, number)` → `Seat(table_id, player_id, position)`. `Seat` è la foglia: una riga per giocatore per tavolo; i punti del turno andranno lì.
- Cancellazione a cascata lungo l'albero della sessione; i giocatori non si cancellano se hanno iscrizioni o posti a sedere (`RESTRICT`): le vecchie sessioni devono restare leggibili con i nomi dell'epoca.
- Nel codice la sessione SQLAlchemy si chiama `db` (`Session as DbSession`) per non confonderla con l'entità `Session`.

## 2026-08-29 — Ciclo di vita della sessione

- Al massimo una sessione `open` alla volta: crearne una nuova chiude automaticamente la precedente (il frontend avvisa: "La nuova sessione chiuderà automaticamente quella vecchia"). La sessione resta aperta finché non viene chiusa manualmente o sostituita.
- Flusso: crea sessione (data, turni) → iscrivi i partecipanti (anagrafica esistente o nome nuovo) → "Genera tavoli" (minimo 6 iscritti) → gioca → chiudi.
- Iscrizioni modificabili solo a sessione aperta e tavoli non ancora generati. Il ritardatario non è previsto: si rifà la sessione.
- Errori del service: `ValueError` per input non valido (400), `SessionStateError` per operazione non ammessa nello stato corrente (409), `LookupError` per giocatore inesistente (404).
- Nessuna migrazione DB per ora: a ogni cambio di schema in sviluppo si cancella `Backend/data/serate.db`.
- Entità `GameTable` invece di `Table` per non collidere con `sqlalchemy.Table`.
- SQLite con `PRAGMA foreign_keys=ON` forzato a ogni connessione (di default SQLite ignora le foreign key).
- File DB in `Backend/data/serate.db`, escluso da git. Test su DB in memoria.

## 2026-08-29 — API HTTP

- FastAPI + uvicorn, server locale su `127.0.0.1:8000`, tutto offline. Endpoint sotto `/api`.
- `create_app(db_path)` come factory: il modulo `main` espone `app` per uvicorn, i test costruiscono un'app su DB in memoria (`StaticPool`, una sola connessione condivisa tra i thread).
- I router traducono soltanto: `ValueError` dei service → 400 (dati non validi) o 409 (giocatore duplicato); risorsa assente → 404. Validazione di forma (campi, range) delegata a Pydantic → 422.
- `EveningRead` restituisce l'albero `rounds → tables → players` già nella forma della griglia; `EveningSummary` (lista) omette i turni.
- CORS aperto solo agli origin del dev server Vite; sparirà quando il backend servirà il frontend compilato.
- Test API con `TestClient` (richiede `httpx`, solo in dev).

## 2026-08-29 — Frontend

- React 19 + Vite, JavaScript, componenti funzionali con hook. ESLint con la configurazione del template Vite.
- **Redux Toolkit** (`configureStore`, `createSlice`, `createAsyncThunk`) per lo stato condiviso: scelta didattica, allineata ai corsi seguiti dall'autore. Tre slice: `navigation` (schermata corrente), `players`, `evenings`. Lo stato locale dei form resta in `useState`. Nessun router: la navigazione è nello slice `navigation`.
- **Tailwind CSS v4** tramite plugin Vite; token del progetto (colori, font display) definiti in `@theme` dentro `src/index.css`, così le utility hanno nomi parlanti (`bg-felt`, `text-muted`).
- Struttura: `src/app/store.js`, `src/features/<nome>/<nome>Slice.js`, `src/api/client.js` (unico punto che parla col backend), `src/pages/*Page.jsx`, `src/components/`, `src/utils/`.
- In sviluppo Vite gira su `:5173` e inoltra `/api` a uvicorn su `:8000`; il codice usa sempre URL relativi, così non cambia quando il backend servirà il build statico.
- Solo font di sistema: l'app deve funzionare offline e impacchettata.
- La griglia della serata riproduce il foglio Excel del gruppo: una riga per turno con linguetta colorata (arancio/giallo/verde come l'originale, poi altri colori a ciclo), una scheda per tavolo, tavoli da 3 con bordo tratteggiato.
- `utils/tables.js` replica `table_sizes` solo per l'anteprima "N tavoli da 4 e M da 3" prima di creare la serata; il backend resta l'unica fonte di verità.
- Testi dell'interfaccia in italiano; date formattate con `Intl` in `it-IT`.
- Express valutato e scartato: sarebbe un secondo backend accanto a FastAPI.

## 2026-08-29 — Convenzioni

- Comandi Python sempre nella forma `python -m pip` / `python -m pytest`: su Windows gli eseguibili in `.venv/Scripts` possono essere bloccati dall'antivirus.
- Nomi di file Python unici in tutto il progetto (eccetto `__init__.py`): i service finiscono in `_service.py`, i router in `_router.py`.
- I percorsi in testa ai file sono relativi alla root del repository e vanno rispettati tali e quali, compresi i `__init__.py` vuoti.

## Aperto

- Anagrafica: "pulisci anagrafica" e una sezione Opzioni. Un giocatore con storia non si cancella, si nasconde (flag `archived`), così le vecchie sessioni restano leggibili.
- Serata "a criteri" (tavoli per classifica dal turno 2): funzione separata nel dominio, da progettare quando si affronta il punteggio.
- Packaging desktop: da decidere (PyInstaller + frontend statico servito da FastAPI è l'ipotesi di partenza).
