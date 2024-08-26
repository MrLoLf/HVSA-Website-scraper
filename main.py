# !/usr/bin/env python3

"""
@Author: Fabian Roscher
@Description: This script is the main entry point for the HVSA-Handball-Scraper.
It loads the configuration from the config.toml file, then it uses the hvsa_requests.py
module to get the league districts for the year specified in the config file.
"""

import asyncio
from config import Config
import config
from hvsa_requests import HvsaRequests
from games import Games
import pyexcel_ods3
from datetime import datetime, timedelta

def save_games_to_ods(games: list[Games], home_team: str) -> bool:
    # Initialize the ODS data structure
    ods_data = {}

    # Sort games by date
    games.sort(key=lambda game: datetime.strptime(game.date, '%d.%m.%Y'))

    # Determine the first and last game dates
    first_game_date = datetime.strptime(games[0].date, '%d.%m.%Y')
    last_game_date = datetime.strptime(games[-1].date, '%d.%m.%Y')

    # Calculate weekends from the first game date to the last game date
    current_date = first_game_date
    weekends = []
    while current_date <= last_game_date:
        if current_date.weekday() == 5:  # Saturday
            weekends.append(current_date)
        current_date += timedelta(days=1)

    # Organize games by weekends
    games_by_weekend = {weekend: [] for weekend in weekends}
    for game in games:
        game_date = datetime.strptime(game.date, '%d.%m.%Y')
        for weekend in weekends:
            if weekend <= game_date < weekend + timedelta(days=2):
                games_by_weekend[weekend].append(game)
                break

    # Create a single sheet for all weekends
    sheet_data = [['Weekend', 'Day', 'Date', 'Time', 'Sports Hall', 'Sports Hall URL', 'Home Team', 'Guest Team']]
    for weekend, weekend_games in games_by_weekend.items():
        weekend_str = weekend.strftime('%d-%m-%Y')
        for game in weekend_games:
            # only save home games for team
            if game.home_team == home_team:
                sheet_data.append([
                    weekend_str,
                    game.day,
                    game.date,
                    game.time,
                    game.sports_hall,
                    game.sports_hall_url,
                    game.home_team,
                    game.guest_team
                ])
    ods_data['Games'] = sheet_data

    # Save the ODS file
    try:
        pyexcel_ods3.save_data("games.ods", ods_data)
        return True
    except Exception as e:
        print(e)
        return False



async def main() -> None:
    config_instance: Config = config.load_config()
    year: str = config_instance.year
    req: HvsaRequests = HvsaRequests(year)
    games:list[Games] = await req.get_district_team_league_id_team_table_games_list('West','Männer','TSV Wefensleben')
    save_games_to_ods(games, 'TSV Wefensleben')

if __name__ == '__main__':
    asyncio.run(main())
