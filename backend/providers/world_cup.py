from __future__ import annotations
import logging
import re
import requests
import warnings
warnings.filterwarnings("ignore")

from backend.config import API_FOOTBALL_KEY
from .base import (
    DataProvider, Match, MatchStats, TeamStats,
    PlayerStat, Shot, Lineup
)

_BASE_URL = "https://v3.football.api-sports.io"

_LEAGUES = [
    {"id": 1,  "season": 2026, "name": "FIFA World Cup 2026",     "is_warmup": False},
    {"id": 10, "season": 2026, "name": "International Friendlies", "is_warmup": True},
]

# Matches any team name containing an age group (U17, U-17, U20, U-20, etc.)
# Word boundary ensures "Uruguay" is not caught. Hyphen variant covers some
# API-Football naming styles (e.g. "England U-21").
_YOUTH = re.compile(r'\bU-?\d{2}\b', re.IGNORECASE)


class WorldCupProvider(DataProvider):
    def __init__(self):
        self._headers = {"x-apisports-key": API_FOOTBALL_KEY}

    def _get(self, path: str, params: dict) -> dict:
        resp = requests.get(
            f"{_BASE_URL}/{path}",
            headers=self._headers,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def _get_stat(self, stat_list: list[dict], name: str, cast, default=0):
        for s in stat_list:
            if s.get("type") == name:
                val = s.get("value")
                if val is None:
                    return default
                try:
                    cleaned = str(val).replace("%", "").strip()
                    return cast(cleaned)
                except (ValueError, TypeError):
                    return default
        return default

    def _parse_fixtures(self, fixtures: list[dict], league: dict) -> list[Match]:
        matches = []
        for f in fixtures:
            fixture = f.get("fixture", {})
            teams = f.get("teams", {})
            goals = f.get("goals", {})
            label = (
                f"{teams['home']['name']} {goals.get('home', 0)}–"
                f"{goals.get('away', 0)} {teams['away']['name']} | "
                f"{league['name']} {league['season']}"
            )
            matches.append(Match(
                match_id="apf:" + str(fixture["id"]),
                label=label,
                home_team=teams["home"]["name"],
                away_team=teams["away"]["name"],
                home_score=int(goals.get("home") or 0),
                away_score=int(goals.get("away") or 0),
                date=str(fixture.get("date", ""))[:10],
                competition=league["name"],
                season=str(league["season"]),
                country="International",
                is_live=True,   # "Live" means current-season provider, not in-progress
                is_warmup=league["is_warmup"],
            ))
        return matches

    def _parse_match_stats(
        self, home_team: str, away_team: str, response: list[dict]
    ) -> MatchStats:
        team_stats: dict[str, list[dict]] = {}
        for entry in response:
            team_stats[entry["team"]["name"]] = entry.get("statistics", [])

        def _extract(team: str) -> TeamStats:
            s = team_stats.get(team, [])
            return TeamStats(
                possession=self._get_stat(s, "Ball Possession", float),
                shots=self._get_stat(s, "Total Shots", int),
                shots_on_target=self._get_stat(s, "Shots on Goal", int),
                passes=self._get_stat(s, "Total passes", int),
                pass_accuracy=self._get_stat(s, "Passes %", float),
                corners=self._get_stat(s, "Corner Kicks", int),
                fouls=self._get_stat(s, "Fouls", int),
            )

        return MatchStats(
            home_team=home_team,
            away_team=away_team,
            home=_extract(home_team),
            away=_extract(away_team),
        )

    def _parse_fbref_shots(self, df, match: Match | None) -> list[Shot] | None:
        try:
            if df is None or df.empty:
                return None
            # Filter to this specific match by team names if match metadata is available
            if match is not None and "squad" in df.columns:
                teams = {match.home_team, match.away_team}
                df = df[df["squad"].isin(teams)]
            if df.empty:
                return None
            shots = []
            for _, row in df.iterrows():
                shots.append(Shot(
                    player=str(row.get("player", "")),
                    team=str(row.get("squad", "")),
                    minute=int(row.get("minute", 0) or 0),
                    xg=float(row.get("xg", 0.0) or 0.0),
                    outcome=str(row.get("outcome", "")),
                    x=float(row.get("x", 0.0) or 0.0),
                    y=float(row.get("y", 0.0) or 0.0),
                ))
            return shots if shots else None
        except Exception as e:
            logging.warning("FBref shot parse failed: %s", e)
            return None

    def get_matches(self) -> list[Match]:
        all_matches = []
        for league in _LEAGUES:
            try:
                data = self._get("fixtures", {"league": league["id"], "season": league["season"]})
                fixtures = [
                    f for f in data.get("response", [])
                    if f.get("fixture", {}).get("status", {}).get("short") == "FT"
                    and not _YOUTH.search(f.get("teams", {}).get("home", {}).get("name", ""))
                    and not _YOUTH.search(f.get("teams", {}).get("away", {}).get("name", ""))
                ]
                all_matches.extend(self._parse_fixtures(fixtures, league))
            except Exception as e:
                logging.warning("Failed to fetch league %s: %s", league["id"], e)
        all_matches.sort(key=lambda m: m.date, reverse=True)
        return all_matches

    def get_match_stats(self, match_id: str) -> MatchStats:
        stats_data = self._get("fixtures/statistics", {"fixture": match_id.removeprefix("apf:")})
        response = stats_data.get("response", [])
        if len(response) < 2:
            raise ValueError(f"No stats available for match {match_id}")
        home_team = response[0]["team"]["name"]
        away_team = response[1]["team"]["name"]
        return self._parse_match_stats(home_team, away_team, response)

    def get_player_stats(self, match_id: str) -> list[PlayerStat]:
        data = self._get("fixtures/players", {"fixture": match_id.removeprefix("apf:")})
        stats = []
        for team_entry in data.get("response", []):
            team_name = team_entry["team"]["name"]
            for player_entry in team_entry.get("players", []):
                p = player_entry.get("player", {})
                s_list = player_entry.get("statistics", [{}])
                s = s_list[0] if s_list else {}
                games = s.get("games", {})
                rating_raw = games.get("rating")
                goals_s = s.get("goals") or {}
                passes_s = s.get("passes") or {}
                shots_s = s.get("shots") or {}
                tackles_s = s.get("tackles") or {}
                stats.append(PlayerStat(
                    player_name=str(p.get("name", "")),
                    team=team_name,
                    rating=float(rating_raw) if rating_raw else None,
                    minutes=int(games.get("minutes") or 0),
                    goals=int(goals_s.get("total") or 0),
                    assists=int(goals_s.get("assists") or 0),
                    shots=int(shots_s.get("total") or 0),
                    key_passes=int(passes_s.get("key") or 0),
                    tackles=int(tackles_s.get("total") or 0),
                    interceptions=int(tackles_s.get("interceptions") or 0),
                ))
        return stats

    def get_shot_data(self, match_id: str) -> list[Shot] | None:
        """Attempt FBref fetch. Returns None if data not yet available."""
        try:
            import soccerdata as sd
            # Look up team names so we can filter FBref data by match
            matches = self.get_matches()
            match = next((m for m in matches if m.match_id == match_id), None)
            fbref = sd.FBref(leagues="World Cup", seasons=2026)
            shots_df = fbref.read_shot_events()
            return self._parse_fbref_shots(shots_df, match)
        except Exception as e:
            logging.info("FBref not yet available for match %s: %s", match_id, e)
            return None

    def get_lineup(self, match_id: str) -> Lineup:
        data = self._get("fixtures/lineups", {"fixture": match_id.removeprefix("apf:")})
        response = data.get("response", [])
        home_entry = response[0] if response else {}
        away_entry = response[1] if len(response) > 1 else {}

        def _players(entry: dict) -> list[str]:
            return [p["player"]["name"] for p in entry.get("startXI", [])]

        return Lineup(
            home_team=home_entry.get("team", {}).get("name", ""),
            away_team=away_entry.get("team", {}).get("name", ""),
            home_formation=home_entry.get("formation", ""),
            away_formation=away_entry.get("formation", ""),
            home_players=_players(home_entry),
            away_players=_players(away_entry),
        )
