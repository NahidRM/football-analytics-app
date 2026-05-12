# data_loader.py
#
# PURPOSE: All StatsBomb API calls live here.
# @st.cache_data tells Streamlit: "once you've fetched this, remember it".
# This means the app doesn't re-fetch the same match data every time the
# user clicks a button — it serves the cached result instead. Faster app,
# fewer unnecessary network calls.

import streamlit as st
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')


@st.cache_data
def get_competitions():
    """Return all available StatsBomb competitions as a DataFrame."""
    return sb.competitions()


@st.cache_data
def get_matches(competition_id: int, season_id: int):
    """Return all matches for a given competition and season."""
    return sb.matches(competition_id=competition_id, season_id=season_id)


@st.cache_data
def get_events(match_id: int):
    """Return all events for a given match."""
    return sb.events(match_id=match_id)
