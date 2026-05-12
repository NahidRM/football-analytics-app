# test_data_loader.py
#
# These are integration tests — they hit the real StatsBomb API.
# Run with: pytest tests/test_data_loader.py -v
# Expected runtime: ~15-30 seconds total (network calls)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd

# We import the raw statsbombpy functions directly (not through data_loader)
# because data_loader uses @st.cache_data which requires a running Streamlit app.
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')


def test_competitions_returns_dataframe():
    comps = sb.competitions()
    assert isinstance(comps, pd.DataFrame)


def test_competitions_has_required_columns():
    comps = sb.competitions()
    required = {'competition_id', 'season_id', 'competition_name', 'season_name'}
    assert required.issubset(set(comps.columns))


def test_matches_returns_dataframe_for_known_competition():
    # Premier League 2003/04: competition_id=2, season_id=44
    matches = sb.matches(competition_id=2, season_id=44)
    assert isinstance(matches, pd.DataFrame)
    assert len(matches) > 0


def test_matches_has_required_columns():
    matches = sb.matches(competition_id=2, season_id=44)
    required = {'match_id', 'home_team', 'away_team', 'home_score', 'away_score'}
    assert required.issubset(set(matches.columns))


def test_events_returns_dataframe_for_known_match():
    events = sb.events(match_id=3749448)
    assert isinstance(events, pd.DataFrame)
    assert len(events) > 0


def test_events_has_required_columns():
    events = sb.events(match_id=3749448)
    required = {'type', 'team', 'player', 'location', 'minute'}
    assert required.issubset(set(events.columns))


def test_events_contains_expected_event_types():
    events = sb.events(match_id=3749448)
    event_types = set(events['type'].unique())
    for expected in ['Pass', 'Shot', 'Pressure']:
        assert expected in event_types, f"Expected event type '{expected}' not found"
