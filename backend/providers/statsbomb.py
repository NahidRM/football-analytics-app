from __future__ import annotations
import logging
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from statsbombpy import sb

from .base import (
    DataProvider, Match, MatchStats, TeamStats,
    PlayerStat, Shot, Lineup
)

# StatsBomb free competitions to expose
_COMPETITIONS = [
    (2, 44),    # Premier League 2003/04
    (2, 90),    # Premier League 2015/16
    (11, 1),    # La Liga 2004/05
    (16, 4),    # Champions League 2018/19
    (37, 42),   # FA Women's Super League 2018/19
    (55, 43),   # UEFA Euro 2020
]

_COUNTRY = {
    2: "England",    # Premier League
    11: "Spain",     # La Liga
    16: "Europe",    # Champions League
    37: "England",   # FA WSL
    55: "Europe",    # Euro 2020
}


class StatsBombProvider(DataProvider):
    def get_matches(self) -> list[Match]:
        rows = []
        comp_df = sb.competitions()
        for comp_id, season_id in _COMPETITIONS:
            try:
                df = sb.matches(competition_id=comp_id, season_id=season_id)
                comp_row = comp_df[
                    (comp_df["competition_id"] == comp_id) &
                    (comp_df["season_id"] == season_id)
                ]
                comp_name = comp_row.iloc[0]["competition_name"] if not comp_row.empty else ""
                season_name = comp_row.iloc[0]["season_name"] if not comp_row.empty else ""
                suffix = f"{comp_name} {season_name}"

                for _, row in df.iterrows():
                    label = (
                        f"{row['home_team']} {int(row['home_score'])}–"
                        f"{int(row['away_score'])} {row['away_team']} | {suffix}"
                    )
                    rows.append(Match(
                        match_id="sb:" + str(int(row["match_id"])),
                        label=label,
                        home_team=str(row["home_team"]),
                        away_team=str(row["away_team"]),
                        home_score=int(row["home_score"]),
                        away_score=int(row["away_score"]),
                        date=str(row["match_date"])[:10],
                        competition=comp_name,
                        season=season_name,
                        country=_COUNTRY.get(comp_id, ""),
                        is_live=False,
                    ))
            except Exception as e:
                logging.warning("Skipping competition %s/%s: %s", comp_id, season_id, e)
                continue
        rows.sort(key=lambda m: m.date, reverse=True)
        return rows

    def get_match_stats(self, match_id: str) -> MatchStats:
        events = sb.events(match_id=int(match_id.removeprefix("sb:")))
        # Get home/away from match metadata rather than guessing from event order
        matches = self.get_matches()
        match = next((m for m in matches if m.match_id == match_id), None)
        if match:
            home_team, away_team = match.home_team, match.away_team
        else:
            teams = events["team"].dropna().unique().tolist()
            home_team = teams[0] if teams else "Home"
            away_team = teams[1] if len(teams) > 1 else "Away"

        def _team_stats(team: str) -> TeamStats:
            te = events[events["team"] == team]
            shots = te[te["type"] == "Shot"]
            on_target = shots[shots["shot_outcome"].isin(["Goal", "Saved"])]
            all_passes = te[te["type"] == "Pass"]
            passes = all_passes[all_passes["pass_outcome"].isna()]
            acc = len(passes) / max(len(all_passes), 1) * 100
            corners = 0
            if "pass_type" in te.columns:
                corners = len(te[(te["type"] == "Pass") & (te["pass_type"] == "Corner")])
            return TeamStats(
                possession=0.0,
                shots=len(shots),
                shots_on_target=len(on_target),
                passes=len(all_passes),
                pass_accuracy=round(acc, 1),
                corners=corners,
                fouls=len(te[te["type"] == "Foul Committed"]),
            )

        return MatchStats(
            home_team=home_team,
            away_team=away_team,
            home=_team_stats(home_team),
            away=_team_stats(away_team),
        )

    def get_player_stats(self, match_id: str) -> list[PlayerStat]:
        events = sb.events(match_id=int(match_id.removeprefix("sb:")))
        players = events[events["player"].notna()][["player", "team"]].drop_duplicates()
        stats = []
        for _, row in players.iterrows():
            pe = events[events["player"] == row["player"]]
            shots = pe[pe["type"] == "Shot"]
            goals = shots[shots["shot_outcome"] == "Goal"]
            key_passes = 0
            if "pass_goal_assist" in pe.columns:
                key_passes = len(pe[(pe["type"] == "Pass") & (pe["pass_goal_assist"].notna())])
            assists = 0
            if "pass_goal_assist" in pe.columns:
                assists = len(pe[(pe["type"] == "Pass") & (pe["pass_goal_assist"] == True)])

            stats.append(PlayerStat(
                player_name=str(row["player"]),
                team=str(row["team"]),
                rating=None,
                minutes=90,
                goals=len(goals),
                assists=assists,
                shots=len(shots),
                key_passes=key_passes,
                tackles=len(pe[pe["type"] == "Tackle"]),
                interceptions=len(pe[pe["type"] == "Interception"]),
            ))
        return stats

    def get_shot_data(self, match_id: str) -> list[Shot] | None:
        events = sb.events(match_id=int(match_id.removeprefix("sb:")))
        shots_df = events[events["type"] == "Shot"]
        if shots_df.empty:
            return []
        shots = []
        for _, row in shots_df.iterrows():
            loc = row.get("location")
            x, y = (loc[0], loc[1]) if isinstance(loc, list) and len(loc) >= 2 else (0.0, 0.0)
            shots.append(Shot(
                player=str(row.get("player", "")),
                team=str(row.get("team", "")),
                minute=int(row.get("minute", 0)),
                xg=float(row.get("shot_statsbomb_xg", 0.0) or 0.0),
                outcome=str(row.get("shot_outcome", "")),
                x=float(x),
                y=float(y),
            ))
        return shots

    def get_lineup(self, match_id: str) -> Lineup:
        lineups = sb.lineups(match_id=int(match_id.removeprefix("sb:")))
        teams = list(lineups.keys())
        home_team = teams[0] if teams else "Home"
        away_team = teams[1] if len(teams) > 1 else "Away"

        def _starters(team: str) -> list[str]:
            df = lineups.get(team, pd.DataFrame())
            if df.empty:
                return []
            if "positions" in df.columns:
                starters = df[df["positions"].apply(
                    lambda p: isinstance(p, list) and len(p) > 0
                )]
                return starters["player_name"].tolist()[:11]
            return df["player_name"].tolist()[:11]

        return Lineup(
            home_team=home_team,
            away_team=away_team,
            home_formation="",
            away_formation="",
            home_players=_starters(home_team),
            away_players=_starters(away_team),
        )
