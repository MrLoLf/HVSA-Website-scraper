from attr import dataclass


@dataclass
class Games:
    """
    A data class to store information about a game.

    Attributes:
        date (str): The date of the game.
        time (str): The time of the game.
        home_team (str): The name of the home team.
        guest_team (str): The name of the guest team.
        sports_hall (str): The name of the sports hall where the game is played.
        sports_hall_url (str): The URL of the sports hall.
        section (str): The section or category of the game.
        league (str): The league in which the game is played.
    """
    day: str
    date: str
    time: str
    sports_hall: int
    sports_hall_url: str
    nr: int
    home_team: str
    guest_team: str
    league: str
    section: str
