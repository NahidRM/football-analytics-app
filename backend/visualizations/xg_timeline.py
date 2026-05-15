from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.providers.base import Shot

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_GRID = "#2a2a4e"
_HOME_COLOR = "#e94560"
_AWAY_COLOR = "#4fc3f7"
_TEXT = "#e0e0e0"


def draw_xg_timeline(
    shots: list[Shot],
    home_team: str,
    away_team: str,
    match_label: str,
) -> plt.Figure:
    """Cumulative xG by minute for both teams. Goals marked with vertical dashed lines."""
    minutes = list(range(0, 92))

    def _cumulative(team: str) -> list[float]:
        xg_by_min: dict[int, float] = {m: 0.0 for m in minutes}
        for s in shots:
            if s.team == team:
                m = min(int(s.minute), 91)
                xg_by_min[m] += s.xg
        cum = 0.0
        curve = []
        for m in minutes:
            cum += xg_by_min[m]
            curve.append(cum)
        return curve

    home_xg = _cumulative(home_team)
    away_xg = _cumulative(away_team)
    max_xg = max(max(home_xg, default=0.0), max(away_xg, default=0.0), 0.5)

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_PLOT_BG)

    ax.plot(minutes, home_xg, color=_HOME_COLOR, linewidth=2.5,
            label=f"{home_team} xG")
    ax.plot(minutes, away_xg, color=_AWAY_COLOR, linewidth=2.5,
            label=f"{away_team} xG")

    for s in shots:
        if s.outcome == "Goal":
            color = _HOME_COLOR if s.team == home_team else _AWAY_COLOR
            ax.axvline(x=s.minute, color=color, linestyle="--", linewidth=1, alpha=0.6)
            ax.text(s.minute + 0.5, max_xg * 0.05,
                    s.player.split()[-1], color=color,
                    fontsize=7, rotation=90, va="bottom")

    ax.set_xlim(0, 91)
    ax.set_ylim(0, None)
    ax.set_xlabel("Minute", color=_TEXT)
    ax.set_ylabel("Cumulative xG", color=_TEXT)
    ax.tick_params(colors=_TEXT)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(color=_GRID, linewidth=0.5, alpha=0.5)
    ax.legend(frameon=False, labelcolor=_TEXT)
    ax.set_title(f"xG Timeline\n{match_label}", color=_TEXT, fontsize=12)
    fig.tight_layout()
    return fig
