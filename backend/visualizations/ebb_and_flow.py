from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

from backend.providers.base import Shot
from backend.config import CLUB_COLORS, FALLBACK_COLOR

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_GRID = "#2a2a4e"
_TEXT = "#e0e0e0"
_SUBTEXT = "#888888"
_NEUTRAL = "#444466"

_BLOCK_SIZE = 10  # minutes per block


def draw_ebb_and_flow(
    shots: list[Shot],
    home_team: str,
    away_team: str,
    match_label: str,
) -> plt.Figure:
    """xG differential by 10-minute block. Bars above = home dominant, below = away."""
    home_color = CLUB_COLORS.get(home_team, FALLBACK_COLOR)
    away_color = CLUB_COLORS.get(away_team, FALLBACK_COLOR)

    # Determine blocks covering the match (always 0-90, plus 90+ if needed)
    max_minute = max((s.minute for s in shots), default=90)
    n_blocks = max(9, (max_minute // _BLOCK_SIZE) + 1)
    blocks = list(range(n_blocks))

    home_xg: dict[int, float] = defaultdict(float)
    away_xg: dict[int, float] = defaultdict(float)

    for s in shots:
        block = min(s.minute // _BLOCK_SIZE, n_blocks - 1)
        if s.team == home_team:
            home_xg[block] += s.xg
        else:
            away_xg[block] += s.xg

    diffs = [home_xg[b] - away_xg[b] for b in blocks]
    max_abs = max((abs(d) for d in diffs), default=0.3)

    labels = [f"{b * _BLOCK_SIZE}–{min((b + 1) * _BLOCK_SIZE, 90)}" for b in blocks]
    # Last label: 90+ if match went to extra time
    if n_blocks > 9:
        labels[-1] = "90+"

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_PLOT_BG)

    x = list(range(len(blocks)))
    for i, d in enumerate(diffs):
        color = home_color if d >= 0 else away_color
        ax.bar(i, d, color=color, alpha=0.85, width=0.75,
               edgecolor="white", linewidth=0.3, zorder=3)

    ax.axhline(0, color=_NEUTRAL, linewidth=1.2, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=_TEXT, fontsize=9, rotation=0)
    ax.tick_params(colors=_TEXT)
    ax.set_ylabel("xG Differential", color=_TEXT, fontsize=10)
    ax.set_ylim(-max_abs * 1.5, max_abs * 1.5)

    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(axis="y", color=_GRID, linewidth=0.5, alpha=0.5, zorder=0)

    # Legend patches
    home_patch = mpatches.Patch(color=home_color, label=home_team, alpha=0.85)
    away_patch = mpatches.Patch(color=away_color, label=away_team, alpha=0.85)
    ax.legend(handles=[home_patch, away_patch], frameon=False,
              labelcolor=_TEXT, fontsize=9, loc="upper right")

    ax.set_title(f"Match Ebb & Flow (xG per 10 minutes)\n{match_label}",
                 color=_TEXT, fontsize=11, pad=10)
    fig.tight_layout()
    return fig
