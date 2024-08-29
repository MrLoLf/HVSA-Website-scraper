from dataclasses import dataclass


@dataclass
class Table:
    """
    A data class to store information about a team's performance in a league.

    Attributes:
        rang (int): The rank of the team in the league.
        team (str): The name of the team.
        url (str): The URL to the team's page.
        encounter (int): The number of encounters (games) played by the team.
        wins (int): The number of games won by the team.
        draws (int): The number of games drawn by the team.
        looses (int): The number of games lost by the team.
        goals_scored (int): The number of goals scored by the team.
        goals_received (int): The number of goals received by the team.
        goal_difference (int): The goal difference (goals scored minus goals received).
        points (str): The points accumulated by the team.
    """
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
