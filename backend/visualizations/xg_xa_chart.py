from __future__ import annotations
import matplotlib.pyplot as plt
from collections import defaultdict

from backend.providers.base import Shot
from backend.config import CLUB_COLORS, FALLBACK_COLOR

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_GRID = "#2a2a4e"
_TEXT = "#e0e0e0"
_SUBTEXT = "#888888"


def _compute_player_xg_xa(shots: list[Shot], team: str) -> list[dict]:
    """Derive per-player xG and xA from shot events."""
    xg: dict[str, float] = defaultdict(float)
    xa: dict[str, float] = defaultdict(float)

    for s in shots:
        if s.team != team:
            continue
        xg[s.player] += s.xg
        if s.assisting_player:
            xa[s.assisting_player] += s.xg

    all_players = set(xg) | set(xa)
    result = [
        {"player": p, "xg": xg[p], "xa": xa[p]}
        for p in all_players
        if p and (xg[p] > 0 or xa[p] > 0)
    ]
    return sorted(result, key=lambda d: d["xg"] + d["xa"])


def draw_xg_xa_chart(
    shots: list[Shot],
    team: str,
    match_label: str,
) -> plt.Figure:
    """Horizontal stacked bar: xG (dark) + xA (light) per player, sorted by total."""
    players_data = _compute_player_xg_xa(shots, team)
    team_color = CLUB_COLORS.get(team, FALLBACK_COLOR)

    import matplotlib.colors as mc
    # Lighter shade for xA: mix team color with white at 50% opacity
    try:
        rgba = mc.to_rgba(team_color)
        xa_color = (rgba[0], rgba[1], rgba[2], 0.38)
    except Exception:
        xa_color = (0.9, 0.1, 0.1, 0.38)

    fig, ax = plt.subplots(figsize=(10, max(4, len(players_data) * 0.65 + 1.5)))
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_PLOT_BG)

    if not players_data:
        ax.text(0.5, 0.5, "No shot data available", ha="center", va="center",
                color=_SUBTEXT, fontsize=13, transform=ax.transAxes)
        ax.set_title(f"Player xG + xA — {team}\n{match_label}",
                     color=_TEXT, fontsize=11, pad=10)
        fig.tight_layout()
        return fig

    names = [d["player"].split()[-1] if " " in d["player"] else d["player"]
             for d in players_data]
    xg_vals = [d["xg"] for d in players_data]
    xa_vals = [d["xa"] for d in players_data]

    y = list(range(len(players_data)))
    ax.barh(y, xg_vals, color=team_color, height=0.6,
            label="xG", edgecolor=_PLOT_BG, linewidth=0.3, zorder=3)
    ax.barh(y, xa_vals, left=xg_vals, color=xa_color, height=0.6,
            label="xA", edgecolor=_PLOT_BG, linewidth=0.3, zorder=3)

    # Total label at end of bar
    for i, d in enumerate(players_data):
        total = d["xg"] + d["xa"]
        if total > 0.01:
            ax.text(total + 0.008, i, f"{total:.2f}",
                    va="center", color=_TEXT, fontsize=8.5)

    ax.set_yticks(y)
    ax.set_yticklabels(names, color=_TEXT, fontsize=10)
    ax.tick_params(colors=_TEXT)
    ax.set_xlabel("Expected Goals / Expected Assists", color=_SUBTEXT, fontsize=9)
    ax.xaxis.set_tick_params(labelcolor=_SUBTEXT)

    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(axis="x", color=_GRID, linewidth=0.5, alpha=0.5, zorder=0)

    # Legend
    from matplotlib.patches import Patch
    handles = [Patch(color=team_color, label="xG (expected goals)"),
               Patch(color=xa_color, label="xA (expected assists)")]
    ax.legend(handles=handles, frameon=False, labelcolor=_TEXT,
              fontsize=9, loc="lower right")

    ax.set_title(f"Player xG + xA — {team}\n{match_label}",
                 color=_TEXT, fontsize=11, pad=10)
    fig.tight_layout()
    return fig
