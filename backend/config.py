import os
from dotenv import load_dotenv

load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")

# ── CLUB COLORS ───────────────────────────────────────────────────────────────
# Official primary colors for each club. Add new clubs here — all scripts
# will pick them up automatically via CLUB_COLORS.get(TEAM, FALLBACK_COLOR).
CLUB_COLORS = {
    'Arsenal':              '#EF0107',
    'Liverpool':            '#C8102E',
    'Chelsea':              '#034694',
    'Manchester City':      '#6CABDD',
    'Manchester United':    '#DA291C',
    'Tottenham Hotspur':    '#132257',
    'Newcastle United':     '#241F20',
    'Aston Villa':          '#95BFE5',
    'West Ham United':      '#7A263A',
    'Barcelona':            '#A50044',
    'Real Madrid':          '#FEBE10',
    'Bayern München':       '#DC052D',
    'Borussia Dortmund':    '#FDE100',
    'Paris Saint-Germain':  '#003F8A',
}

FALLBACK_COLOR = '#333333'   # used when a club isn't in CLUB_COLORS yet

# ── PITCH STYLE ───────────────────────────────────────────────────────────────
# Shared visual theme across all scripts. Change here to update all outputs.
PITCH_COLOR  = '#F0F2F5'   # cool light grey
FIGURE_COLOR = '#F0F2F5'
LINE_COLOR   = '#aaaaaa'   # subtle grey pitch markings
LINE_ALPHA   = 0.6
ACCENT_COLOR = '#222222'   # text, arrows, borders

# ── PRESS MAP ─────────────────────────────────────────────────────────────────
# Press maps always use purple — visually distinct from player heat maps.
# Purple signals defensive stubbornness regardless of which team is analysed.
PRESS_COLOR = '#7B2FBE'

# ── SHOT MAP ──────────────────────────────────────────────────────────────────
GOAL_COLOR = '#00C853'     # bright green — universally reads as "success"
