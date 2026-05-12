# test_visualizations.py
#
# Smoke tests for visualization functions.
# Verifies: each draw_* function runs without crashing and returns a Figure.
# Run with: pytest tests/test_visualizations.py -v
# Expected runtime: ~10-15 seconds (one network call to load events, then local drawing)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import matplotlib
matplotlib.use('Agg')   # non-interactive backend — no pop-up windows during tests
import matplotlib.pyplot as plt
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')

from passing_network import draw_passing_network
from heat_map import draw_heat_map
from shot_map import draw_shot_map
from press_map import draw_press_map

MATCH_LABEL = 'Arsenal 4–2 Liverpool | Premier League 2003/04'


@pytest.fixture(scope='module')
def events():
    """Load match events once and share across all tests in this module."""
    return sb.events(match_id=3749448)


def test_draw_passing_network_returns_figure(events):
    fig = draw_passing_network(events, 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_heat_map_returns_figure(events):
    fig = draw_heat_map(events, 'Thierry Henry', 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_heat_map_raises_for_unknown_player(events):
    with pytest.raises(ValueError, match="No touch events found"):
        draw_heat_map(events, 'Fake Player', 'Arsenal', MATCH_LABEL)


def test_draw_shot_map_returns_figure(events):
    fig = draw_shot_map(events, 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_press_map_returns_figure(events):
    fig = draw_press_map(events, 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
