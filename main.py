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
import logging
import csv
from openpyxl import Workbook


# Configure logging
logging.basicConfig(level=logging.INFO)

def sort_games(games: list[Games]) -> list[Games]:

    """
    Sorts the games by date and time.

    Args:
        games (list[Games]): A list of games to be sorted.

    Returns:
        list[Games]: The sorted list of games.
    """

    time_regex = re.compile(r'[\d:]+')
    date_regex = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')

    # Fill missing dates with the previous entry's date
    previous_date = None
    for gam in games:
        if not date_regex.search(gam.date):
            gam.date = previous_date
        else:
            previous_date = gam.date

    # Sort the games list
    games.sort(key=lambda gam: (
        datetime.strptime(date_regex.search(gam.date).group() if date_regex.search(gam.date) else '01.01.1970', '%d.%m.%Y'),
        datetime.strptime(time_regex.search(gam.time).group() if time_regex.search(gam.time) else '00:00', '%H:%M')
    ))

    return games

def export_games_to_ods(games: list[Games], file_path: str) -> bool:
    """
    Save the provided games to an ODS file.

    Args:
        games (list[Games]): A list of games to be saved.
        file_path (list[str]): A list of home team names.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    if games is None:
        logging.debug("No games provided.")
        return False
    if not games:
        logging.debug("Empty games list.")
        return False
    if file_path is []:
        logging.debug("Home teams not specified.")
        return False

    # Initialize the ODS data structure
    ods = OpenDocumentSpreadsheet()

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
        if os.path.exists(f"{file_path}.ods"):
            os.remove(f"{file_path}.ods")
        ods.save(f"{file_path}.ods")
        logging.info(f"File {file_path}.ods saved successfully.")
        return True
    except Exception as e:
        logging.info(f"Error saving file: {e}")
        return False

def export_games_to_csv(games: list[Games], file_path: str) -> bool:
    """
    Exports the games to a CSV file.

    Args:
        games (list[Games]): A list of games to be exported.
        file_path (str): The path to the CSV file.

    Returns:
        bool: True if the export was successful, False otherwise.
    """
    try:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write the header
            writer.writerow(['Date', 'Time', 'Home Team', 'Guest Team', 'Sports Hall', 'Sports Hall URL', 'Section', 'League'])
            # Write the game data
            for game in games:
                writer.writerow([game.date, game.time ,game.home_team, game.guest_team, game.sports_hall, game.sports_hall_url, game.section, game.league])
        logging.info(f"Games successfully exported to {file_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to export games to CSV: {e}")
        return False

def export_games_to_xlsx(games: list[Games], file_path: str) -> bool:
    try:
        # Create a new workbook and select the active worksheet
        workbook = Workbook()
        sheet = workbook.active

        # Write the headers
        headers = ['Date', 'Time', 'Home Team', 'Guest Team', 'Sports Hall', 'Sports Hall URL', 'Section', 'League']
        sheet.append(headers)

        # Write the game data
        for game in games:
            sheet.append([game.date, game.time ,game.home_team, game.guest_team, game.sports_hall, game.sports_hall_url, game.section, game.league])

        # Save the workbook to the specified file path
        workbook.save(file_path)
        logging.info(f"Games successfully exported to {file_path}")
        return True
    except Exception as e:
        logging.info(f"An error occurred: {e}")
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
    req: HvsaRequests = HvsaRequests(year, logging.INFO)
    sections: dict[str, list[dict[str, str]]] = await req.get_league_sections_league_id(league_id)
    if sections is None:
        logging.debug('No sections found')
        return None
    tasks = []
    for section, _ in sections.items():
        logging.debug(f'Getting games for {team_name} in section {section} and league {league_id}')
        tasks.append(req.get_section_team_league_id_team_table_games_list(league_id, section, team_name))

    results = await asyncio.gather(*tasks)

    games: list[Games] = []
    for i, result in enumerate(results):
        section = list(sections.keys())[i]
        if result is None or result == []:
            logging.debug(f'No games found for {team_name} in section {section} and league {league_id}')
            continue
        logging.info(f'Extending games with result from section {section} for team {team_name} in league {league_id}')
        games.extend(result)
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
    games = sort_games(games)
    export_games_to_ods(games, teams[0])
    export_games_to_csv(games, 'games.csv')
    export_games_to_xlsx(games, 'games.xlsx')

if __name__ == '__main__':
    asyncio.run(main())
