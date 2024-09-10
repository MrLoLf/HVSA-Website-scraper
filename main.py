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

def sort_games(games: set[Games]) -> list[Games]:

    """
    Sorts the games by date and time.

    Args:
        games (set[Games]): A set of games to be sorted.

    Returns:
        list[Games]: The sorted list of games.
    """

    time_regex = re.compile(r'[\d:]+')
    date_regex = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')

    # Fill missing dates with the previous entry's date
    previous_date = None
    new_games_list = []
    for gam in games:
        if not date_regex.match(gam.date):
            new_game = Games(
                date=previous_date,
                time=gam.time,
                day=gam.day,
                sports_hall=gam.sports_hall,
                sports_hall_url=gam.sports_hall_url,
                nr=gam.nr,
                home_team=gam.home_team,
                guest_team=gam.guest_team,
                league=gam.league,
                section=gam.section
            )
        else:
            previous_date = gam.date
            new_game = Games(
                date=gam.date,
                time=gam.time,
                day=gam.day,
                sports_hall=gam.sports_hall,
                sports_hall_url=gam.sports_hall_url,
                nr=gam.nr,
                home_team=gam.home_team,
                guest_team=gam.guest_team,
                league=gam.league,
                section=gam.section
            )
        new_games_list.append(new_game)

    # Sort the games list
    new_games_list.sort(key=lambda gam: (
        datetime.strptime(date_regex.search(gam.date).group() if date_regex.search(gam.date) else '01.01.1970', '%d.%m.%Y'),
        datetime.strptime(time_regex.search(gam.time).group() if time_regex.search(gam.time) else '00:00', '%H:%M')
    ))

    return new_games_list

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
    """
    Export a list of games to an XLSX file.

    Args:
        games (set[Games]): A list of game objects to be exported.
        file_path (str): The path where the XLSX file will be saved.

    Returns:
        bool: True if the export was successful, False otherwise.
    """
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

def export_games_to_html(games: list[Games], file_path: str) -> bool:
    """
    Export a list of games to an HTML file.

    Args:
        games (list[Games]): A list of game objects to be exported.
        file_path (str): The path where the HTML file will be saved.

    Returns:
        bool: True if the export was successful, False otherwise.
    """
    try:
        with open(file_path, 'w') as file:
            # Write the basic HTML structure
            file.write('<!DOCTYPE html>\n')
            file.write('<html lang="en">\n')
            file.write('<head>\n')
            file.write('<meta charset="UTF-8">\n')
            file.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
            file.write('<title>TSV Wefensleben</title>\n')
            file.write('<link rel="stylesheet" href="style.css">\n')
            file.write('<style>\n')
            file.write('table { width: 100%; border-collapse: collapse; }\n')
            file.write('th, td { border: 1px solid black; padding: 8px; text-align: left; }\n')
            file.write('th { background-color: #f2f2f2; }\n')
            file.write('</style>\n')
            file.write('</head>\n')
            file.write('<body>\n')
            file.write('<h1>TSV Wefensleben</h1>\n')
            file.write('<table>\n')
            file.write('<tr>\n')
            file.write('<th>Date</th>\n')
            file.write('<th>Time</th>\n')
            file.write('<th>Home Team</th>\n')
            file.write('<th>Guest Team</th>\n')
            file.write('<th>Sports Hall</th>\n')
            file.write('<th>Section</th>\n')
            file.write('<th>League</th>\n')
            file.write('</tr>\n')

            # Write the game data
            for game in games:
                file.write('<tr>\n')
                file.write(f'<td>{game.date}</td>\n')
                file.write(f'<td>{game.time}</td>\n')
                file.write(f'<td>{game.home_team}</td>\n')
                file.write(f'<td>{game.guest_team}</td>\n')
                file.write(f'<td><a href="{game.sports_hall_url}">{game.sports_hall}</a></td>\n')
                file.write(f'<td>{game.section}</td>\n')
                file.write(f'<td>{game.league}</td>\n')
                file.write('</tr>\n')

            # Close the HTML tags
            file.write('</table>\n')
            file.write('</body>\n')
            file.write('</html>\n')

        logging.info(f"Games successfully exported to {file_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to export games to HTML: {e}")
        return False

async def get_games(year: str, league_id: str, team_name: str) -> set[Games] | None:
    """
    Fetch games for a specific team in a specific league and year.

    Args:
        year (str): The year for which to fetch games.
        league_id (str): The league ID to fetch games for.
        team_name (str): The team name to fetch games for.

    Returns:
        set[Games] | None: A set of games if found, otherwise None.
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
        games.append(result)
    return games

async def get_all_games(year: str, league_ids: set[str], team_names: list[str], team_number: int) -> set[Games]:
    """
    Fetch all games for the given year, league IDs, and team names.

    Args:
        year (str): The year for which to fetch games.
        league_ids (set[str]): A set of league IDs to fetch games for.
        team_names (list[str]): A list of team names to fetch games for.

    Returns:
        set[Games]: A set of games fetched for the given parameters.
    """
    team_counter = 0
    games: list[Games] = []
    while team_number > team_counter:
        tasks = []
        for team_name in team_names:
            for league_id in league_ids:
                if league_id is None:
                    continue
                tasks.append(get_games(year, league_id, team_name))

        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            if result is None or result == []:
                continue

            games.extend(result)
            team_name = team_names[i // len(league_ids)]
            league_id = list(league_ids)[i % len(league_ids)]
            logging.info(f'Extending games with result from section {result[0][0].section} for team {team_name} in league {league_id}')
            team_counter += 1

    set_games = set()
    for game in games:
        for gam in game:
            set_games.add(gam)

    return set_games

async def main() -> None:
    """
    Main entry point of the script. Loads configuration, fetches games, and saves them to an ODS file.
    """
    config_instance: Config = config.load_config()
    year: str = config_instance.year
    teams: list[str] = config_instance.teams
    team_number: int = config_instance.team_number
    req: HvsaRequests = HvsaRequests(year)
    league_ids: set[str] = req.get_league_ids()
    games: set[Games] = await get_all_games(year, league_ids, teams, team_number)
    games: list[Games] = sort_games(games)
    export_games_to_ods(games, teams[0])
    export_games_to_csv(games, 'games.csv')
    export_games_to_xlsx(games, 'games.xlsx')
    export_games_to_html(games, 'index.html')

if __name__ == '__main__':
    asyncio.run(main())
