from attr import dataclass


@dataclass
class Games:
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
