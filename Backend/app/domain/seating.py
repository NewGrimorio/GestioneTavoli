"""Table composition and round generation for a free (non-ranked) evening.

Pure module: no FastAPI, no database. Everything is deterministic given a seed.

Data shapes (kept as plain lists so they serialize trivially):
    Table = list[str]            -> player names seated together
    Round = list[Table]          -> all tables of one round
    Schedule = list[Round]       -> all rounds of the evening
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from itertools import combinations

Table = list[str]
Round = list[Table]
Schedule = list[Round]
Pair = frozenset[str]

MIN_PLAYERS = 6
TABLE_SIZE_PREFERRED = 4
TABLE_SIZE_FALLBACK = 3
DEFAULT_RESTARTS = 30
DEFAULT_KICKS = 20


def table_sizes(n_players: int) -> list[int]:
    """Split ``n_players`` into as many tables of 4 as possible, then tables of 3.

    Tables of 4 come first, tables of 3 last (e.g. ``22 -> [4, 4, 4, 4, 3, 3]``).

    Raises:
        ValueError: if ``n_players`` is below ``MIN_PLAYERS``.
    """
    if n_players < MIN_PLAYERS:
        raise ValueError(f"At least {MIN_PLAYERS} players are required, got {n_players}")
    # n = 4a + 3b with the smallest b: the remainder mod 4 fixes how many
    # tables of 4 must be "downgraded" to tables of 3.
    n_small = (TABLE_SIZE_PREFERRED - n_players % TABLE_SIZE_PREFERRED) % TABLE_SIZE_PREFERRED
    n_large = (n_players - n_small * TABLE_SIZE_FALLBACK) // TABLE_SIZE_PREFERRED
    return [TABLE_SIZE_PREFERRED] * n_large + [TABLE_SIZE_FALLBACK] * n_small


def generate_rounds(
    players: Sequence[str],
    n_rounds: int,
    seed: int | None = None,
    restarts: int = DEFAULT_RESTARTS,
    kicks: int = DEFAULT_KICKS,
) -> Schedule:
    """Generate ``n_rounds`` seatings minimizing repeated encounters between players.

    Rounds are built one after the other. Each round starts from a random deal and
    is refined by an iterated local search: pairwise swaps between tables until no
    improvement remains, then a random perturbation ("kick") and a new descent,
    keeping the perturbed result only if it is better. The best of ``restarts``
    attempts is kept. Encounters already happened are penalized quadratically, so
    when repeats are unavoidable they get spread across many pairs rather than
    concentrated on a few.

    Args:
        players: distinct player names.
        n_rounds: number of rounds to generate (>= 1).
        seed: makes the output reproducible; ``None`` means non-deterministic.
        restarts: random restarts per round; more restarts, better and slower.
        kicks: consecutive non-improving perturbations tolerated before giving up
            on an attempt; ``0`` disables perturbations.

    Raises:
        ValueError: on duplicate players, too few players or invalid parameters.
    """
    names = list(players)
    if len(set(names)) != len(names):
        raise ValueError("Player names must be unique")
    if n_rounds < 1:
        raise ValueError(f"n_rounds must be >= 1, got {n_rounds}")
    if restarts < 1:
        raise ValueError(f"restarts must be >= 1, got {restarts}")
    if kicks < 0:
        raise ValueError(f"kicks must be >= 0, got {kicks}")

    sizes = table_sizes(len(names))
    rng = random.Random(seed)
    meetings: dict[Pair, int] = {}
    schedule: Schedule = []

    for _ in range(n_rounds):
        best_round: Round | None = None
        best_cost = float("inf")
        for _ in range(restarts):
            candidate, cost = _iterated_local_search(names, sizes, meetings, rng, kicks)
            if cost < best_cost:
                best_cost, best_round = cost, candidate
            if best_cost == 0:
                break
        assert best_round is not None
        _record_meetings(best_round, meetings)
        schedule.append(best_round)

    return schedule


def meeting_counts(schedule: Schedule) -> dict[Pair, int]:
    """Count how many times every pair of players shared a table."""
    counts: dict[Pair, int] = {}
    for round_ in schedule:
        _record_meetings(round_, counts)
    return counts


def repeated_meetings(schedule: Schedule) -> int:
    """Total number of encounters beyond the first one, summed over all pairs."""
    return sum(count - 1 for count in meeting_counts(schedule).values() if count > 1)


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #


def _random_round(names: list[str], sizes: list[int], rng: random.Random) -> Round:
    """Deal a shuffled copy of ``names`` into tables of the given sizes."""
    shuffled = names[:]
    rng.shuffle(shuffled)
    round_: Round = []
    offset = 0
    for size in sizes:
        round_.append(shuffled[offset : offset + size])
        offset += size
    return round_


def _perturb(round_: Round, rng: random.Random, n_swaps: int = 2) -> Round:
    """Return a copy of ``round_`` with ``n_swaps`` random cross-table swaps applied."""
    copy = [table[:] for table in round_]
    for _ in range(n_swaps):
        i, j = rng.sample(range(len(copy)), 2)
        ai, bj = rng.randrange(len(copy[i])), rng.randrange(len(copy[j]))
        copy[i][ai], copy[j][bj] = copy[j][bj], copy[i][ai]
    return copy


def _iterated_local_search(
    names: list[str],
    sizes: list[int],
    meetings: dict[Pair, int],
    rng: random.Random,
    kicks: int,
) -> tuple[Round, int]:
    """One attempt: random deal, descent, then kick-and-descend while it keeps paying off."""
    current = _random_round(names, sizes, rng)
    cost = _local_search(current, meetings)
    failed_kicks = 0
    while cost > 0 and failed_kicks < kicks:
        trial = _perturb(current, rng)
        trial_cost = _local_search(trial, meetings)
        if trial_cost < cost:
            current, cost, failed_kicks = trial, trial_cost, 0
        else:
            failed_kicks += 1
    return current, cost


def _record_meetings(round_: Round, counts: dict[Pair, int]) -> None:
    for table in round_:
        for a, b in combinations(table, 2):
            pair = frozenset((a, b))
            counts[pair] = counts.get(pair, 0) + 1


def _pair_weight(a: str, b: str, meetings: dict[Pair, int]) -> int:
    """Cost of seating ``a`` and ``b`` together again: previous encounters squared."""
    n = meetings.get(frozenset((a, b)), 0)
    return n * n


def _table_cost(table: Table, meetings: dict[Pair, int]) -> int:
    return sum(_pair_weight(a, b, meetings) for a, b in combinations(table, 2))


def _player_cost(player: str, table: Table, meetings: dict[Pair, int]) -> int:
    """Cost contributed by ``player`` toward the other members of ``table``."""
    return sum(_pair_weight(player, other, meetings) for other in table if other != player)


def _swap_delta(
    round_: Round, i: int, ai: int, j: int, bj: int, meetings: dict[Pair, int]
) -> int:
    """Change in round cost if player ``ai`` of table ``i`` swaps with ``bj`` of table ``j``."""
    table_i, table_j = round_[i], round_[j]
    a, b = table_i[ai], table_j[bj]
    removed = _player_cost(a, table_i, meetings) + _player_cost(b, table_j, meetings)
    added = _player_cost(b, table_i, meetings) + _player_cost(a, table_j, meetings)
    # ``a`` and ``b`` are never at the same table, so no cross-term correction needed.
    return added - removed


def _local_search(round_: Round, meetings: dict[Pair, int]) -> int:
    """Apply improving pairwise swaps in place until none remains; return final cost."""
    cost = sum(_table_cost(table, meetings) for table in round_)
    improved = True
    while improved and cost > 0:
        improved = False
        for i in range(len(round_)):
            for j in range(i + 1, len(round_)):
                for ai in range(len(round_[i])):
                    for bj in range(len(round_[j])):
                        delta = _swap_delta(round_, i, ai, j, bj, meetings)
                        if delta < 0:
                            round_[i][ai], round_[j][bj] = round_[j][bj], round_[i][ai]
                            cost += delta
                            improved = True
    return cost