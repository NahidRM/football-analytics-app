from __future__ import annotations
import matplotlib.pyplot as plt

from backend.config import CLUB_COLORS, FALLBACK_COLOR

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_GRID = "#2a2a4e"
_TEXT = "#e0e0e0"


def draw_xg_vs_goals(
    home_team: str,
    away_team: str,
    home_xg: float,
    away_xg: float,
    home_score: int,
    away_score: int,
    match_label: str,
) -> plt.Figure:
    """Side-by-side bars comparing xG (expected) vs actual goals for each team."""
    home_color = CLUB_COLORS.get(home_team, FALLBACK_COLOR)
    away_color = CLUB_COLORS.get(away_team, FALLBACK_COLOR)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    fig.patch.set_facecolor(_FIG_BG)

    teams = [(home_team, home_xg, home_score, home_color),
             (away_team, away_xg, away_score, away_color)]

    max_val = max(home_xg, away_xg, home_score, away_score, 1.0)

    for ax, (team, xg, goals, color) in zip(axes, teams):
        ax.set_facecolor(_PLOT_BG)

        ax.bar([0], [xg], color=color, alpha=0.55, width=0.55, zorder=3,
               edgecolor="white", linewidth=0.5)
        ax.bar([1], [goals], color=color, alpha=1.0, width=0.55, zorder=3,
               edgecolor="white", linewidth=0.5)

        # Value labels on top of each bar
        ax.text(0, xg + max_val * 0.03, f"{xg:.2f}",
                ha="center", va="bottom", color=_TEXT, fontsize=13, fontweight="bold")
        ax.text(1, goals + max_val * 0.03, str(goals),
                ha="center", va="bottom", color=_TEXT, fontsize=13, fontweight="bold")

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["xG", "Goals"], color=_TEXT, fontsize=11)
        ax.set_ylim(0, max_val * 1.35)
        ax.tick_params(colors=_TEXT)
        ax.set_title(team, color=color, fontsize=12, fontweight="bold", pad=8)

        for spine in ax.spines.values():
            spine.set_color(_GRID)
        ax.tick_params(left=False, labelleft=False)
        ax.grid(axis="y", color=_GRID, linewidth=0.5, alpha=0.5, zorder=0)

        # Over/under performance label
        diff = goals - xg
        label = f"{'+'}{diff:.2f}" if diff >= 0 else f"{diff:.2f}"
        color_diff = "#00C853" if diff >= 0 else "#FF5252"
        ax.text(0.5, -0.18, f"vs xG: {label}",
                ha="center", va="top", color=color_diff,
                fontsize=10, transform=ax.transAxes)

    fig.suptitle(f"xG vs Goals\n{match_label}", color=_TEXT, fontsize=11, y=1.02)
    fig.tight_layout()
    return fig
