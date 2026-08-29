/**
 * Preview of how N players split into tables. Mirrors `table_sizes` in the
 * backend (as many tables of 4 as possible, then tables of 3) and is used only
 * to show the organizer what they will get before creating the session; the
 * backend remains the source of truth.
 */

export const MIN_PLAYERS = 6;

export function tableSizes(nPlayers) {
  if (nPlayers < MIN_PLAYERS) return [];
  const nSmall = (4 - (nPlayers % 4)) % 4;
  const nLarge = (nPlayers - nSmall * 3) / 4;
  return [...Array(nLarge).fill(4), ...Array(nSmall).fill(3)];
}

/** [4, 4, 3] -> "2 tavoli da 4 e 1 tavolo da 3" */
export function describeTables(sizes) {
  const count = (size) => sizes.filter((s) => s === size).length;
  const label = (n, size) => `${n} ${n === 1 ? "tavolo" : "tavoli"} da ${size}`;
  const parts = [];
  if (count(4)) parts.push(label(count(4), 4));
  if (count(3)) parts.push(label(count(3), 3));
  return parts.join(" e ");
}
