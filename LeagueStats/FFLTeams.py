########################################################################
#                                                                      #
#   FFLTeams.py                                                        #
#   10/25/2013                                                         #
#                                                                      #
#   Object to hold fantasy football team information.  That's all!     #
#                                                                      #
########################################################################



class FantasyTeam():
    """
    Collections of useful information for fantasy football teams
    """
    
    def __init__( self, teamName = None, teamAbb = None, teamID = None ):
        """
        Members include:
            team name
            team abbreviation
            team ID
            roster?
        """
        self.setTeamName( teamName )
        self.setTeamAbb( teamAbb )
        self.setTeamID( teamID )
    
    
    def setTeamName( self, teamName ):
        self.teamName = teamName
    
    
    def setTeamAbb( self, teamAbb ):
        self.teamAbb = teamAbb
    
    
    def setTeamID( self, teamID ):
        self.teamID = teamID


TEAMS = {
    'Dylan'  : FantasyTeam( teamName = 'Shark Nado',              teamAbb = 'SN',   teamID = 1  ),
    'Zach'   : FantasyTeam( teamName = 'Heavy Petting Zoo',       teamAbb = 'HPZ',  teamID = 2  ),
    'Jeff'   : FantasyTeam( teamName = 'Great White Sharts!',     teamAbb = 'ASS',  teamID = 3  ),
    'Collin' : FantasyTeam( teamName = 'I\'d Still Hit It',       teamAbb = 'HIT',  teamID = 4  ),
    'Ben'    : FantasyTeam( teamName = 'Just Noise',              teamAbb = 'JNZ',  teamID = 5  ),
    'Brad'   : FantasyTeam( teamName = 'Chicken Fried Blumpkins', teamAbb = 'CFB',  teamID = 6  ),
    'Jake'   : FantasyTeam( teamName = 'Very European Uppercuts', teamAbb = 'VEU',  teamID = 7  ),
    'Nick'   : FantasyTeam( teamName = 'Gotham City Rogues',      teamAbb = 'GcR',  teamID = 8  ),
    'Dana'   : FantasyTeam( teamName = 'DA lil\' Mookies',        teamAbb = 'LMKS', teamID = 9  ),
    'Andy'   : FantasyTeam( teamName = 'Emergerd! Fertberl!',     teamAbb = 'FVT',  teamID = 10 ),
    'Mike'   : FantasyTeam( teamName = 'Snail Trails',            teamAbb = 'ST',   teamID = 11 ),
    'Matt'   : FantasyTeam( teamName = 'BATH SALTZ',              teamAbb = 'BS',   teamID = 12 )
}
