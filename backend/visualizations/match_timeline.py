from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from backend.providers.base import MatchEvent
from backend.config import CLUB_COLORS, FALLBACK_COLOR

_FIG_BG = "#1a1a2e"
_LINE_COLOR = "#444466"
_TEXT = "#e0e0e0"
_SUBTEXT = "#888888"
_YELLOW = "#FFD700"
_RED = "#FF3333"
_GOAL_COLOR = "#00C853"


def draw_match_timeline(
    events: list[MatchEvent],
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    match_label: str,
) -> plt.Figure:
    """Horizontal timeline showing goals, cards, and substitutions for both teams."""
    home_color = CLUB_COLORS.get(home_team, "#e94560")
    away_color = CLUB_COLORS.get(away_team, "#4fc3f7")

    max_minute = 95
    for e in events:
        total = e.minute + e.extra_time
        if total > max_minute:
            max_minute = total + 2

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_FIG_BG)
    ax.set_xlim(-3, max_minute + 3)
    ax.set_ylim(-4.5, 4.5)
    ax.axis("off")

    # Center line
    ax.axhline(0, color=_LINE_COLOR, linewidth=1.5, zorder=1)
    # Minute ticks
    for m in range(0, max_minute + 1, 15):
        ax.axvline(m, color=_LINE_COLOR, linewidth=0.5, alpha=0.4, zorder=1)
        ax.text(m, -0.35, str(m) + "'", ha="center", va="top",
                color=_SUBTEXT, fontsize=7.5)
    # Halftime line
    ax.axvline(45, color=_LINE_COLOR, linewidth=1, linestyle="--", alpha=0.6, zorder=1)

    # Team labels
    ax.text(-2, 2.0, home_team, ha="right", va="center", color=home_color,
            fontsize=9, fontweight="bold")
    ax.text(-2, -2.0, away_team, ha="right", va="center", color=away_color,
            fontsize=9, fontweight="bold")

    home_event_count: dict[int, int] = {}
    away_event_count: dict[int, int] = {}

    for e in events:
        minute = e.minute + e.extra_time
        is_home = e.team == home_team
        side = 1 if is_home else -1
        color = home_color if is_home else away_color
        counts = home_event_count if is_home else away_event_count
        # Stack events at same minute so they don't overlap
        slot = counts.get(minute, 0)
        counts[minute] = slot + 1
        y_base = side * 1.8
        y = y_base + side * slot * 0.7

        if e.event_type == "Goal":
            # Star marker + player name
            ax.scatter(minute, y, marker="*", s=220, color=_GOAL_COLOR,
                       zorder=4, edgecolors="white", linewidth=0.5)
            label = e.player.split()[-1] if e.player else ""
            ax.text(minute, y + side * 0.75, f"{label} {e.minute}'",
                    ha="center", va="center" if side < 0 else "bottom",
                    color=_TEXT, fontsize=7.5, zorder=5)

        elif e.event_type == "Card":
            card_color = _YELLOW if "Yellow" in e.detail else _RED
            rect = mpatches.FancyBboxPatch(
                (minute - 0.6, y - 0.55), 1.2, 1.1,
                boxstyle="round,pad=0.05",
                facecolor=card_color, edgecolor="white", linewidth=0.5, zorder=4,
            )
            ax.add_patch(rect)
            label = e.player.split()[-1] if e.player else ""
            ax.text(minute, y + side * 0.85, label,
                    ha="center", va="center" if side < 0 else "bottom",
                    color=_SUBTEXT, fontsize=7, zorder=5)

        elif e.event_type == "subst":
            # Arrow symbol for substitution
            ax.annotate("", xy=(minute, y + side * 0.4), xytext=(minute, y - side * 0.4),
                        arrowprops=dict(arrowstyle="->", color=color, lw=1.2), zorder=4)
            out = e.player.split()[-1] if e.player else ""
            into = e.player_in.split()[-1] if e.player_in else ""
            ax.text(minute, y + side * 1.1, f"↑{into} ↓{out}",
                    ha="center", va="center" if side < 0 else "bottom",
                    color=_SUBTEXT, fontsize=6.5, zorder=5)

    # Score badge
    score_x = max_minute + 1.5
    ax.text(score_x, 2.0, str(home_score), ha="center", va="center",
            color=home_color, fontsize=16, fontweight="bold")
    ax.text(score_x, 0, "–", ha="center", va="center", color=_SUBTEXT, fontsize=12)
    ax.text(score_x, -2.0, str(away_score), ha="center", va="center",
            color=away_color, fontsize=16, fontweight="bold")

    ax.set_title(f"Match Timeline\n{match_label}", color=_TEXT, fontsize=11, pad=10)
    fig.tight_layout()
    return fig
