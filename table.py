from dataclasses import dataclass


@dataclass
class Table:
    rang: int
    team: str
    url: str
    encounter: int
    wins: int
    draws: int
    looses: int
    goals_scored: int
    goals_received: int
    goal_difference: int
    points: str
