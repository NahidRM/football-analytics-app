from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from backend.providers.base import MatchStats

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_HOME_COLOR = "#e94560"
_AWAY_COLOR = "#0f3460"
_TEXT = "#e0e0e0"
_SUBTEXT = "#aaaaaa"


def draw_match_stats(stats: MatchStats, match_label: str) -> plt.Figure:
    """Horizontal mirrored bar chart comparing both teams for each stat."""
    categories = ["Possession %", "Shots", "Shots on Target", "Pass Accuracy %", "Corners", "Fouls"]
    home_vals = [
        stats.home.possession,
        float(stats.home.shots),
        float(stats.home.shots_on_target),
        stats.home.pass_accuracy,
        float(stats.home.corners),
        float(stats.home.fouls),
    ]
    away_vals = [
        stats.away.possession,
        float(stats.away.shots),
        float(stats.away.shots_on_target),
        stats.away.pass_accuracy,
        float(stats.away.corners),
        float(stats.away.fouls),
    ]

    n = len(categories)
    fig, axes = plt.subplots(n, 1, figsize=(10, 8))
    fig.patch.set_facecolor(_FIG_BG)

    for ax, cat, hv, av in zip(axes, categories, home_vals, away_vals):
        ax.set_facecolor(_PLOT_BG)
        total = hv + av if (hv + av) > 0 else 1.0
        home_pct = hv / total

        ax.barh(0, home_pct, color=_HOME_COLOR, height=0.5, align="center")
        ax.barh(0, -(1.0 - home_pct), color=_AWAY_COLOR, height=0.5, align="center")
        ax.set_xlim(-1, 1)
        ax.set_yticks([])
        ax.set_xticks([])

        is_pct = cat in ("Possession %", "Pass Accuracy %")
        home_str = f"{hv:.0f}%" if is_pct else str(int(hv))
        away_str = f"{av:.0f}%" if is_pct else str(int(av))

        ax.text(0.02, 0, home_str, ha="left", va="center",
                color=_TEXT, fontsize=10, fontweight="bold")
        ax.text(-0.02, 0, away_str, ha="right", va="center",
                color=_TEXT, fontsize=10, fontweight="bold")
        ax.text(0, -0.45, cat, ha="center", va="top", color=_SUBTEXT, fontsize=8)

        for spine in ax.spines.values():
            spine.set_visible(False)

    home_patch = mpatches.Patch(color=_HOME_COLOR, label=stats.home_team)
    away_patch = mpatches.Patch(color=_AWAY_COLOR, label=stats.away_team)
    fig.legend(handles=[home_patch, away_patch], loc="upper center",
               ncol=2, frameon=False, labelcolor=_TEXT, fontsize=11)
    fig.suptitle(f"Match Stats\n{match_label}", color=_TEXT, fontsize=12, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig
