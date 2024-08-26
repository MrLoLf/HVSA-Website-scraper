import configparser
from configparser import ConfigParser
from dataclasses import dataclass


@dataclass
class Config:
    year: str

def load_config() -> Config:
    config: ConfigParser = configparser.ConfigParser()
    config.read('config.toml')
    year: str = config.get('HVSA', 'year')
    year = year.replace('/', '%2F')
    return Config(year)
