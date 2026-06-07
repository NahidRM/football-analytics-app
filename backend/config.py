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
    # International / World Cup teams
    'France':               '#002395',
    'England':              '#C8102E',
    'Brazil':               '#009C3B',
    'Argentina':            '#74ACDF',
    'Germany':              '#000000',
    'Spain':                '#AA151B',
    'Portugal':             '#006600',
    'Netherlands':          '#FF6600',
    'Belgium':              '#ED2939',
    'Italy':                '#003399',
    'Uruguay':              '#5EB6E4',
    'Colombia':             '#FCD116',
    'Mexico':               '#006847',
    'United States':        '#B22234',
    'Canada':               '#FF0000',
    'Morocco':              '#C1272D',
    'Senegal':              '#00853F',
    'Japan':                '#BC002D',
    'South Korea':          '#CD2E3A',
    'Korea Republic':       '#CD2E3A',
    'Australia':            '#00843D',
    'Saudi Arabia':         '#006C35',
    'IR Iran':              '#239F40',
    'Iran':                 '#239F40',
    'Croatia':              '#FF0000',
    'Switzerland':          '#FF0000',
    'Serbia':               '#C6363C',
    'Denmark':              '#C60C30',
    'Poland':               '#DC143C',
    'Ecuador':              '#FFD100',
    'Cameroon':             '#007A5E',
    'Ghana':                '#006B3F',
    "Ivory Coast":          '#F77F00',
    "Côte d'Ivoire":        '#F77F00',
    'Tunisia':              '#E70013',
    'Egypt':                '#C8102E',
    'Nigeria':              '#008751',
    'Algeria':              '#006233',
    'Qatar':                '#8D1B3D',
    'Costa Rica':           '#002B7F',
    'Panama':               '#005293',
    'Honduras':             '#0073CF',
    'Jamaica':              '#000000',
    'Türkiye':              '#E30A17',
    'Turkey':               '#E30A17',
    'Ukraine':              '#005BBB',
    'Scotland':             '#003594',
    'Wales':                '#C8102E',
    'Austria':              '#ED2939',
    'Sweden':               '#006AA7',
    'Norway':               '#EF2B2D',
    'Chile':                '#D52B1E',
    'Peru':                 '#D91023',
    'Venezuela':            '#CF142B',
    'Paraguay':             '#D52B1E',
}

FALLBACK_COLOR = '#e94560'   # used when a club isn't in CLUB_COLORS yet

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
