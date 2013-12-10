########################################################################
#                                                                      #
#   FFFetch.py                                                         #
#   10/27/2013                                                         #
#                                                                      #
#   Routine to pull arbitrary information from the ESPN fantasy        #
#   football webpage.                                                  #
#                                                                      #
########################################################################

from bs4 import BeautifulSoup
from urllib import urlopen

#-----------------------#
#   Module Constants    #
#-----------------------#

LEAGUE_NAME = 'Sasquatch Nutz'
LEAGUE_ID = 209006
SEASON_ID = 2013


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
        self.URLDic['leagueId'  ] = str( leagueId )
        self.URLDic['seasonId'  ] = str( seasonId )
    
    
    #---------------------------#
    #   General URL Parsing     #
    #---------------------------#
    
    def fetch( self, urlTag, parseTag ):
        """
        A general wrapper for searches.
            urlTag      -   What URL type do we want to open?
            parseTag    -   given that url, what data are we looking for
        """
        url  = self.fetchURL( urlTag )
        soup = BeautifulSoup( urlopen( url ) )
        
        return self.parseSoup( soup, parseTag )
    
    
    #---------------------------#
    #   URL fetchers            #
    #---------------------------#
    
    def fetchURL( self, urlTag ):
        """
        A wrapper for all urls we hope to fetch
        """
        if urlTag == 'schedule':
            return self.fetchURLSchedule()
        else:
            raise ValueError( 'urlTag {} not supported'.format( urlTag ) )
    
    
    def fetchURLSchedule( self ):
        return 'http://games.espn.go.com/ffl/schedule?leagueId={leagueId:}'.format( **self.URLDic )
    
    
    #---------------------------#
    #   Soup Parsers            #
    #---------------------------#
    
    def parseSoup( self, soup, parseTag ):
        """
        A wrapper for soup searches
        """
        if parseTag == 'seasonScores':
            return self.parseSoupSeasonScores( soup )
        else:
            raise ValueError( 'parseTag {} not supported'.format( parseTag ) )
    
    
    def parseSoupSeasonScores( self, soup ):
        """
        Read the page and create a list of lists a la
            [
                [   Week,   HomeTeam,   AwayTeam,   PointsHome, PointsAway  ]
                [   Week,   HomeTeam,   AwayTeam,   PointsHome, PointsAway  ]
            ]
        """
        retList = []
        
        parentDiv = soup.find_all( "div", "games-fullcol" )[ 0 ]
        scheduleTable = parentDiv.table
        
        def parseTableRow( tr ):
            
            tds = tr.find_all( "td" )
            #print tds
            
            away  = str( tds[ 0 ].text )
            home  = str( tds[ 3 ].text )
            away = away[ : away.find('(') - 1 ]
            home = home[ : home.find('(') - 1 ]
            
            score = str( tds[ 5 ].text )
            try:
                awayScore, homeScore = [ float( el ) for el in score.split( '-' ) ]
            except ValueError as e:
                if 'Box' in str( e ):
                    awayScore, homeScore = 'Box', 'Box'
                elif 'Preview' in str( e ):
                    awayScore, homeScore = 'Preview', 'Preview'
                else:
                    raise e
            
            return [ home, away, homeScore, awayScore ]
            
        for tr in scheduleTable.find_all( "tr" ):
            
            #   Pull header rows
            if tr.has_attr( 'class' ):
                if 'tableHead' in tr[ 'class' ]:
                    currentWeek = tr.td.text
                elif 'tableSubHead' in tr[ 'class' ]:
                    pass
            else:
                #   Should be a schedule element
                if len( tr.text ) > 1:
                    if 'Matchups' in tr.text:
                        return retList
                    else:
                        apList = parseTableRow( tr )
                        if 'Preview' not in apList:
                            retList.append( [ currentWeek ] + apList )
        
        return retList
