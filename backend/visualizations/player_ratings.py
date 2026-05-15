from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from backend.providers.base import PlayerStat, Lineup

_FIG_BG = "#1a1a2e"
_PLOT_BG = "#16213e"
_HIGHLIGHT = "#e94560"
_TEXT = "#e0e0e0"
_SUBTEXT = "#aaaaaa"
_BORDER = "#333355"


def draw_player_ratings(
    player_stats: list[PlayerStat],
    lineup: Lineup,
    team: str,
    match_label: str,
) -> plt.Figure:
    """Grid of starting 11 players with ratings. Top performer card highlighted."""
    players = lineup.home_players if team == lineup.home_team else lineup.away_players
    if not players:
        players = [p.player_name for p in player_stats if p.team == team][:11]

    rating_map = {p.player_name: p.rating for p in player_stats if p.team == team}
    best_rating = max((rating_map.get(p) or 0.0 for p in players), default=0.0)

    COLS = 4
    rows_needed = (len(players) + COLS - 1) // COLS
    CARD_W, CARD_H = 0.85, 0.55
    GAP = 0.1

    fig_w = COLS * (CARD_W + GAP) + GAP
    fig_h = rows_needed * (CARD_H + GAP) + 0.8  # extra for title
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_FIG_BG)
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    for idx, player_name in enumerate(players[:11]):
        col = idx % COLS
        row = idx // COLS
        x = GAP + col * (CARD_W + GAP)
        y = fig_h - 0.8 - (row + 1) * (CARD_H + GAP) + GAP

        rating = rating_map.get(player_name)
        is_best = rating is not None and best_rating > 0 and abs(rating - best_rating) < 0.01

        card_color = _HIGHLIGHT if is_best else _PLOT_BG
        rect = mpatches.FancyBboxPatch(
            (x, y), CARD_W, CARD_H,
            boxstyle="round,pad=0.02",
            facecolor=card_color, edgecolor=_BORDER, linewidth=1,
        )
        ax.add_patch(rect)

        short_name = player_name.split()[-1] if " " in player_name else player_name
        ax.text(x + CARD_W / 2, y + CARD_H * 0.65, short_name,
                ha="center", va="center", color=_TEXT, fontsize=9, fontweight="bold")
        rating_str = f"{rating:.1f}" if rating is not None else "—"
        ax.text(x + CARD_W / 2, y + CARD_H * 0.28, rating_str,
                ha="center", va="center", color=_TEXT, fontsize=13, fontweight="bold")

    ax.set_title(f"Player Ratings — {team}\n{match_label}",
                 color=_TEXT, fontsize=11, pad=12)
    fig.tight_layout()
    return fig
