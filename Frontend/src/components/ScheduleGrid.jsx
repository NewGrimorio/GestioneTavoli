/**
 * The session grid, laid out like the group's spreadsheet: one row per round
 * with a coloured round tab on the left, one card per table.
 */
export default function ScheduleGrid({ rounds }) {
  return (
    <div className="flex flex-col gap-7">
      {rounds.map((round) => (
        <section
          key={round.number}
          className="grid grid-cols-1 items-start gap-4 md:grid-cols-[96px_1fr]"
          aria-labelledby={`round-${round.number}`}
        >
          <h3
            id={`round-${round.number}`}
            className="w-max border-2 border-ink px-2.5 py-2 text-center text-[15px] font-semibold md:w-auto"
            style={{ backgroundColor: roundColor(round.number) }}
          >
            Turno {round.number}
          </h3>
          <ol className="grid grid-cols-[repeat(auto-fill,minmax(170px,1fr))] gap-4">
            {round.tables.map((table) => (
              <li
                key={table.number}
                className={`min-h-[140px] border-2 border-ink bg-white ${
                  table.players.length === 3 ? "border-dashed" : ""
                }`}
              >
                <h4 className="border-b-2 border-ink px-2.5 py-1.5 text-sm font-semibold text-muted">
                  Tavolo {table.number}
                </h4>
                <ul className="divide-y divide-line">
                  {table.players.map((player) => (
                    <li key={player.id} className="px-2.5 py-1.5 text-[17px]">
                      {player.name}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}

// The first three match the spreadsheet's Turno 1/2/3 labels; the rest cycle.
const ROUND_COLORS = ["#F2A93B", "#F0DD4C", "#8FCE5A", "#6FB8DC", "#C39BE0", "#F08A8A"];

function roundColor(number) {
  return ROUND_COLORS[(number - 1) % ROUND_COLORS.length];
}
