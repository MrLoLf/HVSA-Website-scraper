import configparser
from configparser import ConfigParser
from dataclasses import dataclass


@dataclass
class Config:
    """
    A data class to store configuration settings.

    Attributes:
        year (str): The year for which the data is being configured.
        teams (list[str]): A list of team names.
    """
    year: str
    teams: list[str]

def load_config() -> Config:
    """
    Loads the configuration from a 'config.toml' file.

    Returns:
        Config: An instance of the Config data class containing the loaded configuration settings.
    """
    config: ConfigParser = configparser.ConfigParser()
    config.read('config.toml', encoding='utf-8')
    year: str = config.get('HVSA', 'year')
    year = year.replace('/', '%2F').strip()
    teams = [team.strip() for team in config.get('HVSA', 'teams').split(',')]
    return Config(year, teams)
