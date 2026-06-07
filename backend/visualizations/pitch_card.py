from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mplsoccer import Pitch

from backend.providers.base import PlayerStat, Lineup
from backend.config import CLUB_COLORS, FALLBACK_COLOR

_FIG_BG = "#0d1117"
_PITCH_COLOR = "#161b22"
_LINE_COLOR = "#30363d"
_TEXT = "#e6edf3"
_SUBTEXT = "#7d8590"

# Pitch coordinates for each formation row (x on a 105-wide pitch, GK at left)
_ROW_X = {1: 8, 2: 28, 3: 50, 4: 72, 5: 90}

# Y spread for N players in a row (pitch height = 68)
_Y_SPREADS = {
    1: [34.0],
    2: [20.0, 48.0],
    3: [14.0, 34.0, 54.0],
    4: [10.0, 27.0, 41.0, 58.0],
    5: [8.0, 21.0, 34.0, 47.0, 60.0],
    6: [6.0, 17.0, 28.0, 40.0, 51.0, 62.0],
}


def _grid_to_xy(grid: str, all_grids: list[str]) -> tuple[float, float]:
    row, col = map(int, grid.split(":"))
    row_cols = sorted(int(g.split(":")[1]) for g in all_grids if int(g.split(":")[0]) == row)
    n = len(row_cols)
    idx = row_cols.index(col)
    x = _ROW_X.get(row, 8 + row * 18)
    y_opts = _Y_SPREADS.get(n, [34.0])
    y = y_opts[min(idx, len(y_opts) - 1)]
    return float(x), y


def draw_pitch_card(
    player_stats: list[PlayerStat],
    lineup: Lineup,
    team: str,
    match_label: str,
) -> plt.Figure:
    """Players placed at their formation positions on a half-pitch with ratings."""
    players = lineup.home_player_details if team == lineup.home_team else lineup.away_player_details
    rating_map = {p.player_name: p.rating for p in player_stats if p.team == team}
    team_color = CLUB_COLORS.get(team, FALLBACK_COLOR)

    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=_PITCH_COLOR,
        line_color=_LINE_COLOR,
        line_alpha=0.7,
    )
    fig, ax = pitch.draw(figsize=(14, 9))
    fig.patch.set_facecolor(_FIG_BG)

    if not players:
        ax.text(52.5, 40, "No lineup data available", ha="center", va="center",
                color=_SUBTEXT, fontsize=14)
        ax.set_title(f"Lineup — {team}\n{match_label}", color=_TEXT, fontsize=12, pad=12)
        fig.tight_layout()
        return fig

    all_grids = [p["grid"] for p in players if p.get("grid")]

    for pl in players:
        grid = pl.get("grid", "")
        if not grid:
            continue
        x, y = _grid_to_xy(grid, all_grids)
        rating = rating_map.get(pl["name"])

        # Rating determines fill shade: good = team color, low = muted
        fill = team_color if rating and rating >= 6.5 else "#3a3a5a"
        circle = mpatches.Circle(
            (x, y), radius=4.2,
            facecolor=fill, edgecolor="white", linewidth=1.5, zorder=4,
        )
        ax.add_patch(circle)

        # Number badge
        ax.text(x - 2.8, y + 3.0, str(pl["number"]),
                color=_TEXT, fontsize=6, fontweight="bold", zorder=5, ha="center")

        # Rating inside circle
        rating_str = f"{rating:.1f}" if rating else "—"
        ax.text(x, y, rating_str, ha="center", va="center",
                color="white", fontsize=10, fontweight="bold", zorder=5)

        # Player last name below
        last_name = pl["name"].split()[-1] if " " in pl["name"] else pl["name"]
        ax.text(x, y - 6.5, last_name, ha="center", va="top",
                color=_TEXT, fontsize=8.5,
                bbox=dict(facecolor=_FIG_BG, alpha=0.6, edgecolor="none", pad=1),
                zorder=5)

    formation = lineup.home_formation if team == lineup.home_team else lineup.away_formation
    fig.suptitle(f"{team}  ·  {formation}\n{match_label}",
                 color=_TEXT, fontsize=11, y=0.98)
    fig.tight_layout()
    return fig
