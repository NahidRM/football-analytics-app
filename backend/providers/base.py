from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Match:
    match_id: str
    label: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    date: str
    competition: str = ""
    season: str = ""
    country: str = ""
    is_live: bool = False


@dataclass
class TeamStats:
    possession: float
    shots: int
    shots_on_target: int
    passes: int
    pass_accuracy: float
    corners: int
    fouls: int


@dataclass
class MatchStats:
    home_team: str
    away_team: str
    home: TeamStats
    away: TeamStats


@dataclass
class PlayerStat:
    player_name: str
    team: str
    rating: float | None
    minutes: int
    goals: int
    assists: int
    shots: int
    key_passes: int
    tackles: int
    interceptions: int


@dataclass
class Shot:
    player: str
    team: str
    minute: int
    xg: float
    outcome: str
    x: float
    y: float


@dataclass
class Lineup:
    home_team: str
    away_team: str
    home_formation: str
    away_formation: str
    home_players: list[str] = field(default_factory=list)
    away_players: list[str] = field(default_factory=list)


class DataProvider(ABC):
    @abstractmethod
    def get_matches(self) -> list[Match]: ...

    @abstractmethod
    def get_match_stats(self, match_id: str) -> MatchStats: ...

    @abstractmethod
    def get_player_stats(self, match_id: str) -> list[PlayerStat]: ...

    @abstractmethod
    def get_shot_data(self, match_id: str) -> list[Shot] | None:
        """Return None when shot data is not yet available."""
        ...

    @abstractmethod
    def get_lineup(self, match_id: str) -> Lineup: ...
