###############################################################################
#                                                                             #
#   FFFetch.py                                                                #
#   10/27/2013                                                                #
#                                                                             #
#   Routine to pull arbitrary information from the ESPN fantasy               #
#   football webpage.                                                         #
#                                                                             #
###############################################################################

import collections
import re

from bs4 import BeautifulSoup
from urllib import urlopen

#-----------------------#
#   Module Constants    #
#-----------------------#

LEAGUE_NAME = 'Sasquatch Nutz'
LEAGUE_ID = 209006
SEASON_ID = 2013


#-----------------------#
#   My errors           #
#-----------------------#

class NoMatchup(Exception):
    def __init__(self, value=''):
        self.value = value

    def __str__(self, value):
        return repr(self.value)


#-----------------------#
#   Fetcher object      #
#-----------------------#

class FFFetcher():
    """Class designed to go to the ESPN fantasy football webpage and fetch
    various information.  I want it to be general enough that we can
    just supply some tags about what info we want and to return either
    just a string or a pre-parsed list of information.

    """

    def __init__(self, leagueName=LEAGUE_NAME, leagueId=LEAGUE_ID, seasonId=SEASON_ID):
        """Start me up"""
        self.URLDic = {}
        self.URLDic['leagueName'] = leagueName
        self.URLDic['leagueId'] = str(leagueId)
        self.URLDic['seasonId'] = str(seasonId)

    #---------------------------#
    #   General URL Parsing     #
    #---------------------------#

    def fetch(self, urlTag, parseTag, fmtDic={}):
        """A general wrapper for searches.
            urlTag      -   What URL type do we want to open?
            parseTag    -   given that url, what data are we looking for
     0 """
        url = self.fetch_url(urlTag, fmtDic)
        soup = BeautifulSoup(urlopen(url))

        #
        return self.parse_soup(soup, parseTag)

    #---------------------------#
    #   URL fetchers            #
    #---------------------------#

    def fetch_url(self, urlTag, fmtDic={}):
        """A wrapper for all urls we hope to fetch"""
        if urlTag == 'schedule':
            return self.fetch_url_schedule()
        elif urlTag == 'standings':
            return self.fetch_url_standings()
        elif urlTag == 'scoreboard':
            return self.fetch_url_scoreboard_fmt(fmtDic)
        else:
            raise ValueError('urlTag {} not supported'.format(urlTag))

    def fetch_scoreboard(self, week, teamId):
        return self.fetch_url('scoreboard').replace('*TEAMID*', str(teamId)).replace('*SCOREPER*', str(week))

    def fetch_url_schedule(self):
        return 'http://games.espn.go.com/ffl/schedule?leagueId={leagueId:}'.format(**self.URLDic)

    def fetch_url_standings(self):
        return 'http://games.espn.go.com/ffl/standings?leagueId={leagueId:}&seasonId={seasonId:}'.format(**self.URLDic)

    def fetch_url_scoreboard_fmt(self, fmtDic):
        fmtDic['seasonId'] = self.URLDic['seasonId']
        fmtDic['leagueId'] = self.URLDic['leagueId']
        return 'http://games.espn.go.com/ffl/boxscorequick?leagueId={leagueId:}&teamId={teamId:}&scoringPeriodId={scoringPeriodId:}&seasonId={seasonId:}&view=scoringperiod&version=quick'.format(**fmtDic)

    #---------------------------#
    #   Soup Parsers            #
    #---------------------------#

    def parse_soup(self, soup, parseTag):
        """A wrapper for soup searches"""
        if parseTag == 'seasonScores':
            return self.parse_soup_season_scores(soup)
        elif parseTag == 'seasonStandings':
            return self.parse_soup_season_standings(soup)
        elif parseTag == 'playerScores':
            return self.parse_soup_player_scores(soup)
        else:
            raise ValueError('parseTag {} not supported'.format(parseTag))

    def parse_soup_season_scores(self, soup):
        """
        Read the page and create a list of lists a la
            [
                [   Week,   HomeTeam,   AwayTeam,   PointsHome, PointsAway  ]
                [   Week,   HomeTeam,   AwayTeam,   PointsHome, PointsAway  ]
            ]
        """
        retList = []

        parentDiv = soup.find_all("div", "games-fullcol")[0]
        scheduleTable = parentDiv.table

        def parseTableRow(tr):

            tds = tr.find_all("td")

            away = str(tds[0].text)
            home = str(tds[3].text)
            away = away[: away.find('(') - 1]
            home = home[: home.find('(') - 1]

            score = str(tds[5].text)
            try:
                awayScore, homeScore = [float(el) for el in score.split('-')]
            except ValueError as e:
                if 'Box' in str(e):
                    awayScore, homeScore = 'Box', 'Box'
                elif 'Preview' in str(e):
                    awayScore, homeScore = 'Preview', 'Preview'
                else:
                    raise e

            return [home, away, homeScore, awayScore]

        for tr in scheduleTable.find_all("tr"):

            #   Pull header rows
            if tr.has_attr('class'):
                if 'tableHead' in tr['class']:
                    currentWeek = tr.td.text
                elif 'tableSubHead' in tr['class']:
                    pass
            else:
                #   Should be a schedule element
                if len(tr.text) > 1:
                    if 'Matchups' in tr.text or 'Byes' in tr.text:
                        return retList
                    else:
                        apList = parseTableRow(tr)
                        if 'Preview' not in apList:
                            retList.append([currentWeek] + apList)

        return retList

    def parse_soup_season_standings(self, soup):
        """Read the page and create a dic
        {
            teamName : {'WINS':
                        'LOSSES':
                        'TIES':
                        'PF':
                        'PA':}, ...
        }

        """
        retDic = collections.defaultdict(dict)

        scores = self.parse_soup_season_standings_scores(soup)
        standings = self.parse_soup_season_standings_standings(soup)

        for team, teamScores in scores.iteritems():
            retDic[team]['PF'] = teamScores['PF']
            retDic[team]['PA'] = teamScores['PA']

        for team, teamStandings in standings.iteritems():
            retDic[team]['WINS'] = teamStandings['WINS']
            retDic[team]['LOSSES'] = teamStandings['LOSSES']
            retDic[team]['TIES'] = teamStandings['TIES']

        return retDic

    def parse_soup_season_standings_standings(self, soup):
        """Parse the html to get the standings from the four divisional tables

        """
        standings = collections.defaultdict(dict)

        parentDiv = soup.find_all("div", "games-fullcol")[0]
        standingsTable = parentDiv.table

        def parse_table_row(tr):
            tds = tr.find_all("td")

            team = str(tds[0].text)
            wins = int(tds[1].text)
            losses = int(tds[2].text)
            ties = int(tds[3].text)

            return (team, wins, losses, ties)

        trs = (z for z in standingsTable.children if z != '\n')
        for tr in trs:
            tds = (z for z in tr.children if z != '\n' and z.text != u'\xa0')
            for td in tds:
                divisionTable = td.table
                teamRows = (z for z in divisionTable.children if z != '\n')
                for teamRow in teamRows:
                    if teamRow['class'] in [['tableHead'], ['tableSubHead']]:
                        pass
                    else:
                        n, w, l, t = parse_table_row(teamRow)
                        standings[n]['WINS'] = w
                        standings[n]['LOSSES'] = l
                        standings[n]['TIES'] = t

        return standings

    def parse_soup_season_standings_scores(self, soup):
        """Parse the html to get the full statistics and scores

        """
        scores = collections.defaultdict(dict)

        parentDiv = soup.find_all("div", "games-fullcol")[0]
        divisionTables = (parentDiv.find("table", {'id': 'xstandTbl_div{}'.format(i)}) for i in range(0, 4))

        def parse_table_row(tr):
            tds = tr.find_all("td")

            team = str(tds[0].a.text)
            pf = float(tds[1].text)
            pa = float(tds[2].text)

            return (team, pf, pa)

        for divisionTable in divisionTables:
            trs = (x for x in divisionTable.children
                   if x != '\n'
                   and x['class'] not in [['tableHead'], ['tableSubHead']])

            for teamRow in trs:
                team, pf, pa = parse_table_row(teamRow)
                scores[team]['PF'] = pf
                scores[team]['PA'] = pa

        return scores

    def parse_soup_player_scores(self, soup):
        """Go get dem scores buay"""
        scores = collections.defaultdict(dict)

        parentDiv = soup.find_all("div", "games-fullcol")[0]

        # check for matchup
        if 'Matchup not found' in parentDiv.text:
            raise NoMatchup()

        teamScores = parentDiv.find('table', {'id': 'playertable_0'})
        week = parentDiv.find('em').text.upper()
        week += ' - PLAYOFFS' if week.startswith('ROUND') else ''

        scores['TEAM NAME'] = teamScores.tr.text.replace(' Box Score', '')
        if scores['TEAM NAME'] == 'BENCH':
            raise ValueError('fuckit')

        trs = teamScores.find_all('tr', class_=re.compile('playerTableBgRow[01]'))

        def parse_table_row(teamRow):
            tds = teamRow.find_all('td')
            pos = str(tds[0].text)
            pts = float(tds[-1].text) if tds[-1].text != '--' else 0
            return pos, pts

        for teamRow in trs:
            pos, pts = parse_table_row(teamRow)
            scores['{0:} {1:}'.format(week, pos)] = pts

        return scores
