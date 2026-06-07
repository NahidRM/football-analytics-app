import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.providers.base import MatchStats, TeamStats, PlayerStat, Shot, Lineup, MatchEvent
from backend.visualizations.match_stats import draw_match_stats
from backend.visualizations.player_ratings import draw_player_ratings
from backend.visualizations.xg_timeline import draw_xg_timeline
from backend.visualizations.pitch_card import draw_pitch_card
from backend.visualizations.match_timeline import draw_match_timeline
from backend.visualizations.xg_xa_chart import draw_xg_xa_chart
from backend.visualizations.xg_vs_goals import draw_xg_vs_goals
from backend.visualizations.ebb_and_flow import draw_ebb_and_flow
from backend.visualizations.sub_impact import draw_sub_impact


# ── Shared fixtures ────────────────────────────────────────────────────────────

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
        home_player_details=[
            {"name": "Lloris", "number": 1, "position": "GK", "grid": "1:1"},
            {"name": "Pavard", "number": 5, "position": "RB", "grid": "2:4"},
            {"name": "Varane", "number": 4, "position": "CB", "grid": "2:3"},
            {"name": "Upamecano", "number": 2, "position": "CB", "grid": "2:2"},
            {"name": "T. Hernandez", "number": 22, "position": "LB", "grid": "2:1"},
            {"name": "Tchouaméni", "number": 8, "position": "DM", "grid": "3:2"},
            {"name": "Rabiot", "number": 14, "position": "CM", "grid": "3:1"},
            {"name": "Griezmann", "number": 7, "position": "CAM", "grid": "4:1"},
            {"name": "Dembélé", "number": 11, "position": "RW", "grid": "5:3"},
            {"name": "Giroud", "number": 9, "position": "ST", "grid": "5:2"},
            {"name": "Mbappé", "number": 10, "position": "LW", "grid": "5:1"},
        ],
    )


def _make_shots() -> list[Shot]:
    return [
        Shot("Mbappé", "France", 23, 0.45, "Goal", 105.0, 34.0, assisting_player="Griezmann"),
        Shot("Giroud", "France", 67, 0.12, "Saved", 103.0, 40.0),
        Shot("En-Nesyri", "Morocco", 44, 0.31, "Goal", 104.0, 36.0),
        Shot("Mbappé", "France", 78, 0.22, "Saved", 106.0, 32.0, assisting_player="Griezmann"),
    ]


def _make_events() -> list[MatchEvent]:
    return [
        MatchEvent(23, 0, "France", "Goal", "Mbappé", "Normal Goal"),
        MatchEvent(44, 0, "Morocco", "Goal", "En-Nesyri", "Normal Goal"),
        MatchEvent(67, 0, "France", "Card", "Rabiot", "Yellow Card"),
        MatchEvent(72, 0, "France", "subst", "Giroud", "Substitution", player_in="Thuram"),
        MatchEvent(80, 0, "Morocco", "subst", "Sabiri", "Substitution", player_in="Hamdallah"),
    ]


# ── Existing tests (match_stats, player_ratings, xg_timeline) ─────────────────

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


# ── pitch_card ─────────────────────────────────────────────────────────────────

def test_draw_pitch_card_returns_figure():
    fig = draw_pitch_card(
        _make_player_stats(), _make_lineup(), "France",
        "France 2–1 Morocco | WC 2026 QF"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_pitch_card_handles_empty_player_details():
    """When API Football returns no grid data, should render a fallback message."""
    lineup = Lineup(
        home_team="France", away_team="Morocco",
        home_formation="4-3-3", away_formation="4-2-3-1",
        home_players=["Lloris", "Mbappé"],
        away_players=["Bounou", "En-Nesyri"],
        # no home_player_details — simulates missing grid data
    )
    fig = draw_pitch_card(_make_player_stats(), lineup, "France", "France vs Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ── match_timeline ─────────────────────────────────────────────────────────────

def test_draw_match_timeline_returns_figure():
    fig = draw_match_timeline(
        _make_events(), "France", "Morocco", 2, 1,
        "France 2–1 Morocco | WC 2026 QF"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_match_timeline_handles_empty_events():
    fig = draw_match_timeline([], "France", "Morocco", 0, 0, "France 0–0 Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ── xg_xa_chart ───────────────────────────────────────────────────────────────

def test_draw_xg_xa_chart_returns_figure():
    fig = draw_xg_xa_chart(_make_shots(), "France", "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_xg_xa_chart_handles_empty_shots():
    fig = draw_xg_xa_chart([], "France", "France 0–0 Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ── xg_vs_goals ───────────────────────────────────────────────────────────────

def test_draw_xg_vs_goals_returns_figure():
    fig = draw_xg_vs_goals(
        "France", "Morocco", 1.82, 0.95, 2, 1,
        "France 2–1 Morocco | WC 2026 QF"
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_xg_vs_goals_handles_zero_values():
    fig = draw_xg_vs_goals("A", "B", 0.0, 0.0, 0, 0, "A 0–0 B")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ── ebb_and_flow ──────────────────────────────────────────────────────────────

def test_draw_ebb_and_flow_returns_figure():
    fig = draw_ebb_and_flow(_make_shots(), "France", "Morocco", "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_ebb_and_flow_handles_empty_shots():
    fig = draw_ebb_and_flow([], "France", "Morocco", "France 0–0 Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ── sub_impact ────────────────────────────────────────────────────────────────

def test_draw_sub_impact_returns_figure():
    fig = draw_sub_impact(_make_shots(), _make_events(), "France", "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_sub_impact_handles_no_substitutions():
    events_no_subs = [e for e in _make_events() if e.event_type != "subst"]
    fig = draw_sub_impact(_make_shots(), events_no_subs, "France", "France 2–1 Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_sub_impact_handles_empty_shots():
    """Has substitutions but no FBref shot data yet."""
    fig = draw_sub_impact([], _make_events(), "France", "France 2–1 Morocco")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
