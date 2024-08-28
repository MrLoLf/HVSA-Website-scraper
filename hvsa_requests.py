
"""
@Author: Fabian Roscher
@Description: Scraper for hvsa website
@License: MIT
"""

import aiohttp
from bs4 import BeautifulSoup, Tag, ResultSet
from table import Table
from games import Games
import logging


class HvsaRequests:
    __HTTPS: str = 'https://'
    __Domain: str = 'hvsa-handball.liga.nu'
    __HVSA: str = f'{__HTTPS}{__Domain}/cgi-bin/WebObjects/nuLigaHBDE.woa/wa/leaguePage?championship='

    def __init__(self, year: str, log_level=logging.INFO):
        self.year: str = year
        logging.basicConfig(level=log_level)
        self.logger = logging.getLogger(__name__)



    @staticmethod
    def get_league_ids() -> set[str]:
        league_ids: set[str] = {
            'MHV',
            'HVSA',
            'Anhalt',
            'Nord',
            'Süd',
            'West'
        }
        return league_ids


    async def get_league_page_league_id(self, league_id: str) -> str | None:
        url: str = f'{self.__HVSA}{league_id}+{self.year}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.text()

    async def get_league_sections_league_id(self, league_id: str) -> dict[str, list[dict[str, str]]] | None:
        page = await self.get_league_page_league_id(league_id)
        if page is None:
            self.logger.debug(f'No page found for league: {league_id}')
            return None
        return self.__parse_league_sections(page)


    @staticmethod
    def __parse_league_sections(page: str) -> dict[str, list[dict[str, str]]]:
        soup = BeautifulSoup(page, 'html.parser')
        league_section: dict[str, list[dict[str, str]]] = {}
        table: Tag = soup.find('table', {'class': 'matrix'})
        for h2 in table.find_all('h2'):
            h2: Tag
            category = h2.text.strip()
            if category not in league_section:
                league_section[category] = []
            for ul in h2.find_all_next('ul'):
                ul: Tag
                if ul.find_previous('h2') != h2:
                    break
                for li in ul.find_all('li'):
                    li: Tag
                    a_tag = li.find('a')
                    team_name = a_tag.text.strip()
                    team_url = a_tag['href']
                    league_section[category].append({'name': team_name, 'url': team_url})
        return league_section

    async def get_section_teams_league_id_page(self, league_id: str, section: str) -> str | None:
        league_sections = await self.get_league_sections_league_id(league_id)
        if league_sections is None:
            self.logger.debug(f'No section: {section} found for {league_id}')
            return None
        if section in league_sections and  league_sections[section]:
            for entry in league_sections[section]:
                url = self.__HTTPS + self.__Domain + entry['url']
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.text()
        return None

    @staticmethod
    def __parse_section_teams_page(page: str) -> list[Table]:
        soup = BeautifulSoup(page, 'html.parser')
        table_tag: Tag = soup.find('table', {'class': 'result-set'})
        if table_tag is None:
            return []
        rows = table_tag.find_all('tr')[1:]  # Skip the header row

        tables = []
        for row in rows:
            cols = row.find_all('td')
            if cols is None:
                continue
            if len(cols) < 10:
                continue
            rang = int(cols[1].text.strip())
            team = cols[2].text.strip()
            url = cols[2].find('a')['href']
            encounter = int(cols[3].text.strip())
            wins = int(cols[4].text.strip())
            draws = int(cols[5].text.strip())
            looses = int(cols[6].text.strip())
            goals_scored, goals_received = map(int, cols[7].text.strip().split(':'))
            goal_difference = int(cols[8].text.strip())
            points = cols[9].text.strip()

            table = Table(
                rang=rang,
                team=team,
                url= url,
                encounter=encounter,
                wins=wins,
                draws=draws,
                looses=looses,
                goals_scored=goals_scored,
                goals_received=goals_received,
                goal_difference=goal_difference,
                points=points
            )
            tables.append(table)

        return tables


    async def get_section_team_league_id_table(self, league_id: str, section: str) -> list[Table] | None:
        self.logger.debug(f"Fetching section team league ID table for league_id: {league_id}, section: {section}")
        page = await self.get_section_teams_league_id_page(league_id, section)
        if page is None:
            self.logger.debug(f'Didn\'t find {section} for {league_id}')
            return None
        return self.__parse_section_teams_page(page)

    async def get_section_team_league_id_team_table_entry(self, league_id: str, section: str, team_name: str) -> Table | None:
        self.logger.debug(f"Fetching table entry for team: {team_name} in league_id: {league_id}, section: {section}")
        list_table: list[Table] = await self.get_section_team_league_id_table(league_id, section)
        if list_table is None:
            self.logger.debug(f'No table found for {team_name} in {section} for {league_id}')
            return None
        for table in list_table:
            if table.team == team_name:
                self.logger.debug(f"Found table entry for team: {team_name} in league_id: {league_id}, section: {section}")
                return table

        self.logger.debug(f"No table entry found for team: {team_name} in league_id: {league_id}, section: {section}")
        return None

    async def get_section_team_league_id_team_table_games_page(self, league_id: str, section: str, team_name: str) -> str | None:
        self.logger.debug(f"Fetching games page for team: {team_name} in league_id: {league_id}, section: {section}")
        table: Table = await self.get_section_team_league_id_team_table_entry(league_id, section, team_name)
        if table is None:
            self.logger.debug(f'No team found for {team_name} in {section} for {league_id}')
            return None
        url = self.__HTTPS + self.__Domain + table.url
        self.logger.debug(f"Fetching URL: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    self.logger.debug(f"Successfully fetched games page for team: {team_name}")
                    return await response.text()
                else:
                    self.logger.debug(f"Failed to fetch games page for team: {team_name}, status code: {response.status}")
                    return None


    async def get_section_team_league_id_team_table_games_ics(self, league_id: str, section: str, team_name: str) -> str:
        page = await self.get_section_team_league_id_team_table_games_page(league_id, section, team_name)
        soup = BeautifulSoup(page, 'html.parser')
        a = soup.find('a', {'class': 'picto-ical-add'})
        return a['href']

    async def get_section_team_league_id_team_table_games_ics_file(self, league_id: str, section: str, team_name: str) -> bool:
        url: str = await self.get_section_team_league_id_team_table_games_ics(league_id, section, team_name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    with open('./games.ics', 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)

            return True
        except Exception as e:
            print(e)
            return False

    async def get_section_team_league_id_team_table_games_list(self, league_id: str, section: str, team_name: str) -> list[Games] | None:
        page = await self.get_section_team_league_id_team_table_games_page(league_id, section, team_name)
        if page is None:
            self.logger.debug(f'No games found for {team_name} in {section} for {league_id} Page was None!')
            return None
        soup = BeautifulSoup(page, 'html.parser')
        table_tag: ResultSet = soup.find_all('table', {'class': 'result-set'})
        rows = table_tag[1].find_all('tr')[1:]
        games = []
        for row in rows:
            cols = row.find_all('td')
            if cols is None:
                continue
            if len(cols) < 7:
                continue
            day = cols[0].text.strip()
            date = cols[1].text.strip()
            time = cols[2].text.strip()
            sports_hall = cols[3].text.strip()
            try:
                sports_hall_url = cols[3].find('a')['href']
            except TypeError:
                sports_hall_url = ''
            nr = cols[4].text.strip()
            home_team = cols[5].text.strip()
            guest_team = cols[6].text.strip()

            game = Games(
                day=day,
                date=date,
                time=time,
                sports_hall=sports_hall,
                sports_hall_url= self.__HTTPS + self.__Domain + sports_hall_url,
                nr=nr,
                home_team=home_team,
                guest_team=guest_team,
                league=league_id,
                section=section
            )
            games.append(game)
        return games
