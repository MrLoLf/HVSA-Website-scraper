import configparser
from configparser import ConfigParser
from dataclasses import dataclass


@dataclass
class Config:
    year: str
    teams: list[str]

def load_config() -> Config:
    config: ConfigParser = configparser.ConfigParser()
    config.read('config.toml', encoding='utf-8')
    year: str = config.get('HVSA', 'year')
    year = year.replace('/', '%2F').strip()
    teams = [team.strip() for team in config.get('HVSA', 'teams').split(',')]
    return Config(year, teams)
