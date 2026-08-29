import pytest

from app.domain.seating import (
    generate_rounds,
    meeting_counts,
    repeated_meetings,
    table_sizes,
)


def _players(n: int) -> list[str]:
    return [f"P{i:02d}" for i in range(n)]


# --------------------------------------------------------------------------- #
# table_sizes
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (6, [3, 3]),
        (7, [4, 3]),
        (8, [4, 4]),
        (9, [3, 3, 3]),
        (10, [4, 3, 3]),
        (11, [4, 4, 3]),
        (12, [4, 4, 4]),
        (13, [4, 3, 3, 3]),
        (20, [4, 4, 4, 4, 4]),
        (22, [4, 4, 4, 4, 3, 3]),
    ],
)
def test_table_sizes_known_cases(n: int, expected: list[int]) -> None:
    assert table_sizes(n) == expected


@pytest.mark.parametrize("n", range(6, 61))
def test_table_sizes_sum_and_shape(n: int) -> None:
    sizes = table_sizes(n)
    assert sum(sizes) == n
    assert set(sizes) <= {3, 4}
    # Tables of 4 first, never more than three tables of 3.
    assert sizes == sorted(sizes, reverse=True)
    assert sizes.count(3) <= 3


@pytest.mark.parametrize("n", [0, 1, 3, 4, 5])
def test_table_sizes_rejects_too_few_players(n: int) -> None:
    with pytest.raises(ValueError):
        table_sizes(n)


# --------------------------------------------------------------------------- #
# generate_rounds - structure
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("n", [6, 7, 13, 20, 22])
def test_each_round_is_a_partition_with_right_sizes(n: int) -> None:
    players = _players(n)
    schedule = generate_rounds(players, n_rounds=3, seed=1)
    assert len(schedule) == 3
    for round_ in schedule:
        assert [len(t) for t in round_] == table_sizes(n)
        seated = [p for table in round_ for p in table]
        assert sorted(seated) == sorted(players)


def test_seed_makes_output_reproducible() -> None:
    players = _players(22)
    assert generate_rounds(players, 3, seed=42) == generate_rounds(players, 3, seed=42)


def test_different_seeds_give_different_schedules() -> None:
    players = _players(22)
    assert generate_rounds(players, 3, seed=1) != generate_rounds(players, 3, seed=2)


def test_rejects_duplicate_players() -> None:
    with pytest.raises(ValueError):
        generate_rounds(["A", "B", "C", "D", "E", "A"], 1)


@pytest.mark.parametrize("n_rounds", [0, -1])
def test_rejects_invalid_round_count(n_rounds: int) -> None:
    with pytest.raises(ValueError):
        generate_rounds(_players(8), n_rounds)


@pytest.mark.parametrize(("restarts", "kicks"), [(0, 20), (30, -1)])
def test_rejects_invalid_search_parameters(restarts: int, kicks: int) -> None:
    with pytest.raises(ValueError):
        generate_rounds(_players(8), 1, restarts=restarts, kicks=kicks)


# --------------------------------------------------------------------------- #
# generate_rounds - quality
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("seed", range(5))
def test_22_players_3_rounds_no_repeats(seed: int) -> None:
    """The real-life case from the reference evening: 22 players, 3 rounds."""
    schedule = generate_rounds(_players(22), 3, seed=seed)
    assert repeated_meetings(schedule) == 0


@pytest.mark.parametrize("n", [16, 20, 24])
@pytest.mark.parametrize("seed", range(3))
def test_three_rounds_of_full_tables_no_repeats(n: int, seed: int) -> None:
    """16 = 4x4 grid: rows, columns, diagonals give three disjoint rounds, so a
    zero-repeat schedule exists and the search must find it."""
    schedule = generate_rounds(_players(n), 3, seed=seed)
    assert repeated_meetings(schedule) == 0


def test_12_players_3_rounds_stays_near_lower_bound() -> None:
    """Three tables of 4 from three first-round groups: every later table holds
    two players from the same group, so at least 3 repeats per round after the
    first (lower bound 6). The search consistently lands on 9."""
    schedule = generate_rounds(_players(12), 3, seed=0)
    assert 6 <= repeated_meetings(schedule) <= 9


def test_8_players_2_rounds_reaches_theoretical_minimum() -> None:
    """Two tables of 4: any second-round table holds at least two players from the
    same first-round table, so 4 repeated encounters is the provable minimum."""
    schedule = generate_rounds(_players(8), 2, seed=3)
    assert repeated_meetings(schedule) == 4


def test_repeats_are_spread_when_unavoidable() -> None:
    """With many rounds nobody should be stuck with the same partner every time."""
    schedule = generate_rounds(_players(8), 6, seed=7)
    assert max(meeting_counts(schedule).values()) <= 4


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def test_meeting_counts_and_repeats() -> None:
    schedule = [
        [["A", "B", "C"], ["D", "E", "F"]],
        [["A", "B", "D"], ["C", "E", "F"]],
    ]
    counts = meeting_counts(schedule)
    assert counts[frozenset({"A", "B"})] == 2
    assert counts[frozenset({"E", "F"})] == 2
    assert counts[frozenset({"A", "D"})] == 1
    assert repeated_meetings(schedule) == 2