# !/usr/bin/env python3

"""
@Author: Fabian Roscher
@Description: This script is the main entry point for the HVSA-Handball-Scraper.
It loads the configuration from the config.toml file, then it uses the hvsa_requests.py
module to get the league sections for the year specified in the config file.
@License: MIT
"""

import asyncio
from config import Config
import config
from hvsa_requests import HvsaRequests
from games import Games
from datetime import datetime
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P, Span
from odf.style import Style, TextProperties
import os
import re


def save_games_to_ods(games: list[Games], home_teams: list[str]) -> bool:
    """
    Save the provided games to an ODS file.

    Args:
        games (list[Games]): A list of games to be saved.
        home_teams (list[str]): A list of home team names.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    if games is None:
        print("No games provided.")
        return False
    if not games:
        print("Empty games list.")
        return False
    if home_teams is []:
        print("Home team not specified.")
        return False

    # Initialize the ODS data structure
    ods = OpenDocumentSpreadsheet()

    # Sort games by date
    time_regex = re.compile(r'[\d:]+')
    date_regex = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
    games.sort(key=lambda gam: (
        datetime.strptime(date_regex.search(gam.date).group() if date_regex.search(gam.date) else '01.01.1970', '%d.%m.%Y'),
        datetime.strptime(time_regex.search(gam.time).group() if time_regex.search(gam.time) else '00:00', '%H:%M')
    ))
    # Define styles for coloring text
    red_text_style = Style(name="RedText", family="text")
    red_text_style.addElement(TextProperties(color="#FF0000"))
    ods.styles.addElement(red_text_style)

    blue_text_style = Style(name="BlueText", family="text")
    blue_text_style.addElement(TextProperties(color="#0000FF"))
    ods.styles.addElement(blue_text_style)

    green_text_style = Style(name="GreenText", family="text")
    green_text_style.addElement(TextProperties(color="#00FF00"))
    ods.styles.addElement(green_text_style)


    # Create a table
    table = Table(name="Games")

    # Add header row
    header_row = TableRow()
    for header in ["Date", "Time", "Home Team", "Guest Team", "Sports Hall", "Sports Hall URL", "Section", "League"]:
        cell = TableCell()
        cell.addElement(P(text=header))
        header_row.addElement(cell)
    table.addElement(header_row)

    # Add game rows
    for game in games:
        row = TableRow()
        for value in [game.date, game.time, game.home_team, game.guest_team, game.sports_hall, game.sports_hall_url, game.section, game.league]:
            cell = TableCell()
            if value == "2161":
                text_element = P()
                text_element.addElement(Span(text=value, stylename=red_text_style))
            elif value == "1053":
                text_element = P()
                text_element.addElement(Span(text=value, stylename=blue_text_style))
            elif value == "205101":
                text_element = P()
                text_element.addElement(Span(text=value, stylename=green_text_style))
            else:
                text_element = P(text=value)
            cell.addElement(text_element)
            row.addElement(cell)
        table.addElement(row)

    # Add table to document
    ods.spreadsheet.addElement(table)

    # Save the ODS file
    try:
        if os.path.exists(f"{home_teams[0]}_games.ods"):
            os.remove(f"{home_teams[0]}_games.ods")
        ods.save(f"{home_teams[0]}_games.ods")
        print(f"File {home_teams[0]}_games.ods saved successfully.")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False


async def get_games(year: str, league_id: str, team_name: str) -> list[Games] | None:
    """
    Fetch games for a specific team in a specific league and year.

    Args:
        year (str): The year for which to fetch games.
        league_id (str): The league ID to fetch games for.
        team_name (str): The team name to fetch games for.

    Returns:
        list[Games] | None: A list of games if found, otherwise None.
    """
    req: HvsaRequests = HvsaRequests(year)
    sections: dict[str, list[dict[str, str]]] = await req.get_league_sections_league_id(league_id)
    if sections is None:
        print('No sections found')
        return None
    games: list[Games] = []
    for section, _ in sections.items():
        print(f'Getting games for {team_name} in section {section} and league {league_id}')
        games_req: list[Games] = await req.get_section_team_league_id_team_table_games_list(league_id, section, team_name)
        if games_req is None:
            print(f'No games found for {team_name} in section {section} and league {league_id}')
            continue
        games.extend(games_req)
    return games

async def get_all_games(year: str, league_ids: set[str], team_names: list[str]) -> list[Games]:
    """
    Fetch all games for the given year, league IDs, and team names.

    Args:
        year (str): The year for which to fetch games.
        league_ids (set[str]): A set of league IDs to fetch games for.
        team_names (list[str]): A list of team names to fetch games for.

    Returns:
        list[Games]: A list of games fetched for the given parameters.
    """
    tasks = []
    for team_name in team_names:
        for league_id in league_ids:
            if league_id is None:
                continue
            tasks.append(get_games(year, league_id, team_name))

    results = await asyncio.gather(*tasks)

    games = []
    for i, result in enumerate(results):
        if result is None or result == []:
            team_name = team_names[i // len(league_ids)]
            league_id = list(league_ids)[i % len(league_ids)]
            print(f'No games found for team: {team_name} in league: {league_id}')
            continue
        games.extend(result)
    return games

async def main() -> None:
    """
    Main entry point of the script. Loads configuration, fetches games, and saves them to an ODS file.
    """
    config_instance: Config = config.load_config()
    year: str = config_instance.year
    teams: list[str] = config_instance.teams
    req: HvsaRequests = HvsaRequests(year)
    league_ids: set[str] = req.get_league_ids()
    games: list[Games] = await get_all_games(year, league_ids, teams)
    save_games_to_ods(games, teams)

if __name__ == '__main__':
    asyncio.run(main())
