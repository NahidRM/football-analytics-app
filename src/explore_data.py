# explore_data.py
#
# PURPOSE: Get familiar with StatsBomb's free data before building visualizations.
# This script doesn't save anything — it just prints data to the terminal so we
# can understand what we're working with.
#
# WHAT IS STATSBOMB?
# StatsBomb is a football data company that publishes a portion of their data
# for free. It includes detailed "event data" — every single pass, shot, press,
# carry and dribble in a match, each with x/y coordinates on the pitch.
# This is the data that powers heat maps, passing networks, and pressing maps.
#
# HOW TO RUN:
# Make sure your venv is active (you'll see "(venv)" in your terminal), then:
#   python3 src/explore_data.py

# ── IMPORTS ──────────────────────────────────────────────────────────────────
# statsbombpy is the official Python library for accessing StatsBomb data.
# "sb" is just a short alias so we don't have to type "statsbombpy" every time.
from statsbombpy import sb
import pandas as pd

# This just makes pandas print full columns without cutting them off
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)


# ── STEP 1: SEE ALL AVAILABLE COMPETITIONS ───────────────────────────────────
print("=" * 60)
print("STEP 1: AVAILABLE COMPETITIONS IN STATSBOMB FREE DATA")
print("=" * 60)

# sb.competitions() returns a DataFrame (a table) of every competition
# that StatsBomb has made available for free.
competitions = sb.competitions()

# We only want to see the key columns — there are more but these are enough
print(competitions[['competition_id', 'competition_name', 'season_id', 'season_name']].to_string(index=False))

print(f"\nTotal available: {len(competitions)} competition-seasons\n")


# ── STEP 2: LOOK AT ONE COMPETITION IN DETAIL ────────────────────────────────
print("=" * 60)
print("STEP 2: MATCHES FROM A SPECIFIC COMPETITION")
print("=" * 60)

# Let's look at the 2003/04 Premier League season — Arsenal's Invincibles.
# This is one of the most famous EPL seasons ever, and StatsBomb has it for free.
#
# competition_id=2 is the Premier League
# season_id=44 is the 2003/04 season
# (These IDs came from the table printed above)

print("Loading Premier League 2003/04 (Arsenal Invincibles)...\n")
matches = sb.matches(competition_id=2, season_id=44)

# Show key columns about the matches
print(matches[['match_id', 'match_date', 'home_team', 'away_team', 'home_score', 'away_score']].to_string(index=False))
print(f"\nTotal matches: {len(matches)}\n")


# ── STEP 3: PEEK INSIDE ONE MATCH'S EVENT DATA ───────────────────────────────
print("=" * 60)
print("STEP 3: WHAT DOES EVENT DATA LOOK LIKE?")
print("=" * 60)

# Let's grab the first match from that season
first_match = matches.iloc[0]
match_id = first_match['match_id']

print(f"Loading events for: {first_match['home_team']} vs {first_match['away_team']} ({first_match['match_date']})")
print("This may take a few seconds...\n")

events = sb.events(match_id=match_id)

# How many events are in one match?
print(f"Total events in this match: {len(events)}")
print(f"Types of events recorded: {events['type'].nunique()}")
print()

# What types of events exist?
print("EVENT TYPES AND HOW OFTEN THEY APPEAR:")
print(events['type'].value_counts().to_string())
print()

# What columns (pieces of information) do we have for each event?
print("COLUMNS AVAILABLE IN EVENT DATA:")
for col in events.columns:
    print(f"  - {col}")

print()

# Let's look at one specific pass in detail so you can see the raw data structure
print("ONE EXAMPLE PASS (raw data):")
one_pass = events[events['type'] == 'Pass'].iloc[0]
print(one_pass[['type', 'minute', 'player', 'team', 'location', 'pass_end_location', 'pass_length', 'pass_outcome']].to_string())

print()
print("=" * 60)
print("EXPLORATION COMPLETE")
print("This data — locations, players, event types — is what we'll")
print("use to build passing maps, heat maps, and pressing analyses.")
print("=" * 60)
