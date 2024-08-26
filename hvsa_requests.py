
"""
@Author: Fabian Roscher
@Desciption: Scraper for hvsa website
@License: MIT
"""

import aiohttp
from bs4 import BeautifulSoup, Tag, ResultSet
from table import Table
from games import Games


class HvsaRequests:
    __HTTPS: str = 'https://'
    __Domain: str = 'hvsa-handball.liga.nu'
    __HVSA: str = f'{__HTTPS}{__Domain}/cgi-bin/WebObjects/nuLigaHBDE.woa/wa/leaguePage?championship='

    def __init__(self, year: str):
        self.year: str = year


    @staticmethod
    def get_league_ids() -> set[str]:
        league_ids: set[str] = {
            'MHV',
            'HVSA'
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
                response.raise_for_status()
                return await response.text()

    async def get_league_districts_league_id(self, league_id: str) -> dict[str, list[dict[str, str]]] | None:
        page = await self.get_league_page_league_id(league_id)
        if page == None:
            print('No page found')
            return None
        return self.__parse_league_districts(page)


    @staticmethod
    def __parse_league_districts(page: str) -> dict[str, list[dict[str, str]]]:
        soup = BeautifulSoup(page, 'html.parser')
        league_district: dict[str, list[dict[str, str]]] = {}
        table: Tag = soup.find('table', {'class': 'matrix'})
        for h2 in table.find_all('h2'):
            h2: Tag
            category = h2.text.strip()
            if category not in league_district:
                league_district[category] = []
            for ul in h2.find_all_next('ul'):
                ul: Tag
                if ul.find_previous('h2') != h2:
                    break
                for li in ul.find_all('li'):
                    li: Tag
                    a_tag = li.find('a')
                    team_name = a_tag.text.strip()
                    team_url = a_tag['href']
                    league_district[category].append({'name': team_name, 'url': team_url})
        return league_district

    async def get_district_teams_league_id_page(self, league_id: str, district: str) -> str | None:
        league_districts = await self.get_league_districts_league_id(league_id)
        if league_districts is None:
            print('No league found')
            return None
        if district in league_districts and  league_districts[district]:
            for entry in league_districts[district]:
                url = self.__HTTPS + self.__Domain + entry['url']
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.text()
        return None

    @staticmethod
    def __parse_district_teams_page(page: str) -> list[Table]:
        soup = BeautifulSoup(page, 'html.parser')
        table_tag: Tag = soup.find('table', {'class': 'result-set'})
        rows = table_tag.find_all('tr')[1:]  # Skip the header row

        tables = []
        for row in rows:
            cols = row.find_all('td')
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


    async def get_district_team_league_id_table(self, league_id: str, district: str) -> list[Table] | None:
        page = await self.get_district_teams_league_id_page(league_id, district)
        if page == None:
            print('No district found')
            return None
        return self.__parse_district_teams_page(page)

    async def get_district_team_league_id_team_table_entry(self, league_id: str, district: str, team_name: str) -> Table | None:
        list_table: list[Table] = await self.get_district_team_league_id_table(league_id, district)
        if list_table is None:
            print('No table found')
            return None
        for table in list_table:
            if table.team == team_name:
                return table

    async def get_district_team_league_id_team_table_games_page(self, league_id: str, district: str, team_name: str) -> str | None:
        table: Table = await self.get_district_team_league_id_team_table_entry(league_id, district, team_name)
        if table is None:
            print('No team found')
            return None
        url = self.__HTTPS + self.__Domain + table.url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()


    async def get_district_team_league_id_team_table_games_ics(self, league_id: str, district: str, team_name: str) -> str:
        page = await self.get_district_team_league_id_team_table_games_page(league_id, district, team_name)
        soup = BeautifulSoup(page, 'html.parser')
        a = soup.find('a', {'class': 'picto-ical-add'})
        return a['href']

    async def get_district_team_league_id_team_table_games_ics_file(self, league_id: str, district: str, team_name: str) -> bool:
        url: str = await self.get_district_team_league_id_team_table_games_ics(league_id, district, team_name)
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

    async def get_district_team_league_id_team_table_games_list(self, league_id: str, district: str, team_name: str) -> list[Games] | None:
        page = await self.get_district_team_league_id_team_table_games_page(league_id, district, team_name)
        if page == None:
            print('No games found')
            return None
        soup = BeautifulSoup(page, 'html.parser')
        table_tag: ResultSet = soup.find_all('table', {'class': 'result-set'})
        rows = table_tag[1].find_all('tr')[1:]
        games = []
        for row in rows:
            cols = row.find_all('td')
            day = cols[0].text.strip()
            date = cols[1].text.strip()
            time = cols[2].text.strip()
            sports_hall = cols[3].text.strip()
            sports_hall_url = cols[3].find('a')['href']
            nr = cols[4].text.strip()
            home_team = cols[5].text.strip()
            guest_team = cols[6].text.strip()

            game = Games(
                day=day,
                date=date,
                time=time,
                sports_hall=sports_hall,
                sports_hall_url= self.__HTTPS + self.__Domain +sports_hall_url,
                nr=nr,
                home_team=home_team,
                guest_team=guest_team
            )
            games.append(game)
        return games
