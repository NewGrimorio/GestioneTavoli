const longDate = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
});

/** "2026-08-29" -> "sabato 29 agosto 2026" */
export function formatLongDate(isoDate) {
  return longDate.format(parseIsoDate(isoDate));
}

/** Today as "YYYY-MM-DD" in local time (what <input type="date"> expects). */
export function todayIso() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function parseIsoDate(isoDate) {
  // Build the date from its parts to avoid the UTC shift of `new Date("YYYY-MM-DD")`.
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/** "3 turni", "1 turno" */
export function pluralize(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}
