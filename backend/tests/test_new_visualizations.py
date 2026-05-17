import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from backend.providers.base import MatchStats, TeamStats, PlayerStat, Shot, Lineup
from backend.visualizations.match_stats import draw_match_stats
from backend.visualizations.player_ratings import draw_player_ratings
from backend.visualizations.xg_timeline import draw_xg_timeline


def _make_match_stats() -> MatchStats:
    return MatchStats(
        home_team="France",
        away_team="Morocco",
        home=TeamStats(possession=60.0, shots=14, shots_on_target=6,
                       passes=520, pass_accuracy=89.0, corners=5, fouls=12),
        away=TeamStats(possession=40.0, shots=8, shots_on_target=3,
                       passes=340, pass_accuracy=82.0, corners=3, fouls=15),
    )


def _make_player_stats() -> list[PlayerStat]:
    return [
        PlayerStat("Mbappé", "France", 8.9, 90, 1, 1, 5, 3, 1, 0),
        PlayerStat("Griezmann", "France", 7.5, 90, 0, 0, 2, 4, 2, 1),
        PlayerStat("Lloris", "France", 7.2, 90, 0, 0, 0, 0, 0, 0),
        PlayerStat("En-Nesyri", "Morocco", 7.8, 90, 1, 0, 3, 1, 0, 0),
    ]


def _make_lineup() -> Lineup:
    return Lineup(
        home_team="France", away_team="Morocco",
        home_formation="4-3-3", away_formation="4-2-3-1",
        home_players=["Lloris", "Pavard", "Varane", "Upamecano", "T. Hernandez",
                      "Tchouaméni", "Rabiot", "Griezmann", "Dembélé", "Giroud", "Mbappé"],
        away_players=["Bounou", "Hakimi", "Aguerd", "Saiss", "Mazraoui",
                      "Ounahi", "Amrabat", "Ziyech", "Boufal", "En-Nesyri", "Sabiri"],
    )


def _make_shots() -> list[Shot]:
    return [
        Shot("Mbappé", "France", 23, 0.45, "Goal", 105.0, 34.0),
        Shot("Giroud", "France", 67, 0.12, "Saved", 103.0, 40.0),
        Shot("En-Nesyri", "Morocco", 44, 0.31, "Goal", 104.0, 36.0),
    ]


def test_draw_match_stats_returns_figure():
    fig = draw_match_stats(_make_match_stats(), "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_player_ratings_returns_figure():
    fig = draw_player_ratings(
        _make_player_stats(), _make_lineup(), "France",
        "France 2–1 Morocco | WC 2026 QF"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_xg_timeline_returns_figure():
    fig = draw_xg_timeline(
        _make_shots(), "France", "Morocco",
        "France 2–1 Morocco | WC 2026 QF"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_match_stats_handles_zero_values():
    stats = MatchStats(
        home_team="A", away_team="B",
        home=TeamStats(0.0, 0, 0, 0, 0.0, 0, 0),
        away=TeamStats(0.0, 0, 0, 0, 0.0, 0, 0),
    )
    fig = draw_match_stats(stats, "A 0–0 B")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_xg_timeline_handles_empty_shots():
    fig = draw_xg_timeline([], "France", "Morocco", "France 0–0 Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
