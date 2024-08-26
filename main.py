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
import pyexcel_ods3
from datetime import datetime, timedelta
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P, Span
from odf.style import Style, TextProperties
import os



def save_games_to_ods(games: list[Games], home_team: str) -> bool:
    if games is None:
        return False
    if games == []:
        return False
    if home_team == '':
        return False


    # Initialize the ODS data structure
    ods = OpenDocumentSpreadsheet()

    # Sort games by date
    games.sort(key=lambda game: datetime.strptime(game.date, '%d.%m.%Y'))

    # Define styles for coloring text
    red_text_style = Style(name="RedText", family="text")
    red_text_style.addElement(TextProperties(color="#FF0000"))
    ods.styles.addElement(red_text_style)

    blue_text_style = Style(name="BlueText", family="text")
    blue_text_style.addElement(TextProperties(color="#0000FF"))
    ods.styles.addElement(blue_text_style)

    # Create a table
    table = Table(name="Games")

    # Add header row
    header_row = TableRow()
    for header in ["Date", "Time", "Home Team", "Guest Team", "Sports Hall"]:
        cell = TableCell()
        cell.addElement(P(text=header))
        header_row.addElement(cell)
    table.addElement(header_row)

    # Add game rows
    for game in games:
        row = TableRow()
        for value in [game.date, game.time, game.home_team, game.guest_team, game.sports_hall]:
            cell = TableCell()
            if value == "2161":
                text_element = P()
                text_element.addElement(Span(text=value, stylename=red_text_style))
            elif value == "1053":
                text_element = P()
                text_element.addElement(Span(text=value, stylename=blue_text_style))
            else:
                text_element = P(text=value)
            cell.addElement(text_element)
            row.addElement(cell)
        table.addElement(row)

    # Add table to document
    ods.spreadsheet.addElement(table)

    # Save the ODS file
    try:
        if os.path.exists(f"{home_team}_games.ods"):
            os.remove(f"{home_team}_games.ods")
        ods.save(f"{home_team}_games.ods")
        return True
    except Exception as e:
        print(e)
        return False


async def get_games(year: str, league_id: str, team_name: str) -> list[Games] | None:
    req: HvsaRequests = HvsaRequests(year)
    sections: dict[str, list[dict[str, str]]] = await req.get_league_sections_league_id(league_id)
    if sections is None:
        print('No sections found')
        return None
    games: list[Games] = []
    for section, _ in sections.items():
        print(f'Getting games for {team_name} in section {section}')
        games_req: list[Games] = await req.get_section_team_league_id_team_table_games_list('West', section, team_name)
        if games_req is None:
            print(f'No games found for {team_name} in section {section}')
            continue
        games.extend(games_req)
    return games


async def main() -> None:
    config_instance: Config = config.load_config()
    year: str = config_instance.year
    req: HvsaRequests = HvsaRequests(year)
    team = 'TSV Wefensleben'
    games = await get_games(year, 'West', team)
    save_games_to_ods(games, team)

if __name__ == '__main__':
    asyncio.run(main())
