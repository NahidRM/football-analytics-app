from __future__ import annotations
import matplotlib.pyplot as plt

from backend.providers.base import Shot, MatchEvent
from backend.config import CLUB_COLORS, FALLBACK_COLOR

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_GRID = "#2a2a4e"
_TEXT = "#e0e0e0"
_SUBTEXT = "#888888"

_WINDOW = 20  # minutes to look before/after each substitution


def _xg_rate(shots: list[Shot], team: str, start: int, end: int) -> float:
    """xG per 10 minutes in [start, end) for the given team."""
    duration = end - start
    if duration <= 0:
        return 0.0
    total = sum(s.xg for s in shots if s.team == team and start <= s.minute < end)
    return total / duration * 10


def draw_sub_impact(
    shots: list[Shot],
    events: list[MatchEvent],
    team: str,
    match_label: str,
) -> plt.Figure:
    """xG rate before vs after each substitution for the selected team."""
    team_color = CLUB_COLORS.get(team, FALLBACK_COLOR)

    subs = [e for e in events if e.event_type == "subst" and e.team == team]

    fig, ax = plt.subplots(figsize=(max(8, len(subs) * 2.2 + 2), 5))
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_PLOT_BG)

    if not subs or not shots:
        ax.text(0.5, 0.5,
                "No substitution data available" if not subs else "No FBref shot data yet",
                ha="center", va="center", color=_SUBTEXT, fontsize=13,
                transform=ax.transAxes)
        ax.set_title(f"Substitution Impact — {team}\n{match_label}",
                     color=_TEXT, fontsize=11, pad=10)
        fig.tight_layout()
        return fig

    import matplotlib.colors as mc
    try:
        rgba = mc.to_rgba(team_color)
        before_color = (rgba[0], rgba[1], rgba[2], 0.45)
    except Exception:
        before_color = (0.9, 0.1, 0.1, 0.45)

    n = len(subs)
    x = list(range(n))
    width = 0.35
    before_rates, after_rates = [], []

    for sub in subs:
        m = sub.minute
        before = _xg_rate(shots, team, max(0, m - _WINDOW), m)
        after = _xg_rate(shots, team, m, min(120, m + _WINDOW))
        before_rates.append(before)
        after_rates.append(after)

    ax.bar([i - width / 2 for i in x], before_rates, width=width,
           color=before_color, edgecolor="white", linewidth=0.4,
           label=f"Before (–{_WINDOW}′)", zorder=3)
    ax.bar([i + width / 2 for i in x], after_rates, width=width,
           color=team_color, edgecolor="white", linewidth=0.4,
           label=f"After (+{_WINDOW}′)", zorder=3)

    ax.axhline(0, color=_GRID, linewidth=1, zorder=2)

    labels = []
    for sub in subs:
        into = sub.player_in.split()[-1] if sub.player_in else "?"
        out = sub.player.split()[-1] if sub.player else "?"
        labels.append(f"↑{into}\n↓{out}\n{sub.minute}′")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=_TEXT, fontsize=8.5)
    ax.tick_params(colors=_TEXT)
    ax.set_ylabel("xG per 10 min", color=_TEXT, fontsize=9)

    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(axis="y", color=_GRID, linewidth=0.5, alpha=0.5, zorder=0)

    ax.legend(frameon=False, labelcolor=_TEXT, fontsize=9)
    ax.set_title(f"Substitution Impact — {team}\n{match_label}",
                 color=_TEXT, fontsize=11, pad=10)
    fig.tight_layout()
    return fig
