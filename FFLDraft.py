########################################################################
#                                                                      #
#   FFLDraft.py                                                        #
#   8/30/13                                                            #
#                                                                      #
#   Routines used in my fantasy football draft, primarily focused on   #
#   the metric of replacement value -- the difference between a player #
#   and the next best player (that I can get, that is) or the field.   #
#                                                                      #
########################################################################

import scipy
import pylab
pylab.close( 'All' )

#----------------------------------------------------------------------#
#                                                                      #
#   Module Constants                                                   #
#                                                                      #
#----------------------------------------------------------------------#

CSV_DTYPE = [                   \
    ( 'ESPNRank', 'int32' ),    \
    ( 'PlayerFirst', 'S15' ),   \
    ( 'PlayerLast', 'S15' ),    \
    ( 'Team', 'S4' ),           \
    ( 'Pos', 'S4' ),            \
    ( 'FantasyTeam', 'S5' ),    \
    ( 'CompAtt', 'S10' ),       \
    ( 'PassYards', 'int32' ),   \
    ( 'PassTD', 'int32'),       \
    ( 'PassInt', 'int32'),      \
    ( 'RushAtt', 'int32'),      \
    ( 'RushYards', 'int32'),    \
    ( 'RushTD', 'int32'),       \
    ( 'Receptions', 'int32'),   \
    ( 'RecYards', 'int32'),     \
    ( 'RecTD', 'int32'),        \
    ( 'FantPoints', 'float32'), \
    ( 'ReplValue', 'float32')   ]


LEAGUE_TEAMS = {                                                        \
    1   :   [   'SN',              'Shark Nado',   'Dylan Thomson' ],   \
    2   :   [  'HPZ',       'Heavy Petting Zoo',   'Zach Lamberty' ],   \
    3   :   [  'ASS',      'Great White Sharts',     'Jeff Miller' ],   \
    4   :   [  'HIT',       'I\'d Still Hit It',  'Collin Solberg' ],   \
    5   :   [  'JNZ',              'Just Noise',        'Ben Koch' ],   \
    6   :   [  'CFB', 'Chicken Fried Blumpkins',    'Brad Nicolai' ],   \
    7   :   [  'YES',                 'Yes!etc', 'Jake Hillesheim' ],   \
    8   :   [  'GcR',      'Gotham City Rogues',       'Nick Igoe' ],   \
    9   :   [ 'LMKS',        'DA Lil\' Mookies',   'Dana Kinsella' ],   \
    10  :   [  'FVT',     'Emergerd! Fertberl!',    'Andy Warmuth' ],   \
    11  :   [   'ST',            'Snail Trails',   'Michael Lubke' ],   \
    12  :   [   'BS',              'BATH SALTS',    'Matt Hibberd' ]    }

INT_INTEGER_SET = [ 0, 5, 6, 7, 8, 9, 10, 11, 12, 13 ]
FLOAT_INTEGER_SET = [ 14, 15 ]

PREDICTION_DATA_FILE = 'FFLDraftData.csv'

POS_COLOR = {           \
    'K'     :   'm',    \
    'P'     :   'y',    \
    'QB'    :   'k',    \
    'WR'    :   'b',    \
    'RB'    :   'r',    \
    'TE'    :   'g',    \
    'D/ST'  :   'c'     }



#----------------------------------------------------------------------#
#                                                                      #
#   Module Functions                                                   #
#                                                                      #
#----------------------------------------------------------------------#

class DraftData():
    """
    A class object to calculate draft data, who to pick, etc.
    """
    
    def __init__( self ):
        self.loadPredictionData()
        self.updateReplacementValue()
        
        self.f1 = pylab.figure( 1, figsize = [ 7.5, 5.5 ] )
        self.f2 = pylab.figure( 2, figsize = [ 7.5, 5.5 ] )
        
        self.bestReplacementAvailable()
    
    
    def loadPredictionData( self ):
        """
        Open the csv data and load it into an array
        """
        with open( PREDICTION_DATA_FILE, 'rb' ) as f:
            s = f.read()
        
        s = [ row.split(',') + [ 0.0 ] for row in s.split('\n')[:-1] ][1:]
        
        #   Make into integers and floats what is integers and floats,
        #   also strip leading whitespace and split the team/pos into
        #   team, pos
        for i in range( len( s ) ):
            
            #   int
            for j in INT_INTEGER_SET:
                x = s[ i ][ j ]
                if x == '--':
                    s[ i ][ j ] = 0
                else:
                    s[ i ][ j ] = int( s[ i ][ j ] )
            
            #   float
            for j in FLOAT_INTEGER_SET:
                x = s[ i ][ j ]
                if x == '--':
                    s[ i ][ j ] = 0.0
                else:
                    s[ i ][ j ] = float( s[ i ][ j ] )
                
            #   whitespace
            s[ i ][ 2 ] = s[ i ][ 2 ].strip( ' ' )
            
            #   Split team/pos
            teamPos = s[ i ][ 2 ]
            team, pos = teamPos.split( ' ' )
            
            s[ i ] = s[ i ][ :2 ] + [ team, pos ] + s[ i ][ 3: ]
            
            #   Split Name
            firstLast = s[ i ][ 1 ].split( ' ' )
            first = firstLast[ 0 ]
            last = ' '.join( firstLast[1:] )
            
            s[ i ] = s[ i ][ :1 ] + [ first, last ] + s[ i ][ 2: ]
        
        s = [ tuple( row ) for row in s ]
        
        self.predictionData = scipy.array( s, dtype = CSV_DTYPE )
        
    
    #
    #   Updating who has been drafted
    #
    
    def newDraft( self ):
        """
        Prompt the user to choose who has been drafted and on which
        team
        """
        
        #   Ask for last name
        firstNameInit = raw_input( 'First Name Initial?\t' )
        lastNameInit = raw_input(  'Last Name Initial? \t' )
        
        print '\n'
        for row in self.predictionData:
            rank, first, last, team, pos, fantTeam = list( row )[ :6 ]
            firstRight = first.startswith( firstNameInit.lower() ) or ( first.startswith( firstNameInit.upper() ) )
            lastRight = last.startswith( lastNameInit.lower() ) or ( last.startswith( lastNameInit.upper() ) )
            if firstRight and lastRight:
                print str( (rank, first, last, team, pos) )
        
        thisRank = int( raw_input( '\nwhich rank is correct? (0 for none of the above)\t' ) )
        
        if thisRank == 0:
            pass
        else:
            print '\n'
            for (teamID, teamInfo) in LEAGUE_TEAMS.iteritems():
                print str( teamID ) + '\t' + '{:<4}, {:<23}, {:<15}'.format( *teamInfo )
            
            thisTeam = int( raw_input( '\nWhich Team Drafted Him? (0 to break)\t' ) )
            if thisTeam == 0:
                pass
            else:
                thisTeamName = LEAGUE_TEAMS[ thisTeam ][ 0 ]
                
                self.beenDrafted( thisRank, thisTeamName )
    
    
    def beenDrafted( self, rank, fantTeam ):
        """
        Update the array to display who has been drafted by which team
        """
        if self.predictionData[ rank ][ 0 ] == rank:
            self.predictionData[ rank ][ 5 ] = fantTeam
        else:
            for row in self.predictionData:
                if row[ 0 ] == rank:
                    row[ 5 ] = fantTeam
                    break
        
        self.updateReplacementValue()
        self.bestReplacementAvailable()
    
    
    def falseDraft( self ):
        """
        Undo a previous draft that has been rolled back (it always
        happens)
        """
        #   Ask for last name
        firstNameInit = raw_input( 'First Name Initial?\t' )
        lastNameInit = raw_input(  'Last Name Initial? \t' )
        
        print '\n'
        for row in self.predictionData:
            rank, first, last, team, pos, fantTeam = list( row )[ :6 ]
            if first.startswith( firstNameInit ) and last.startswith( lastNameInit ):
                print str( (rank, first, last, team, pos) )
        
        thisRank = int( raw_input( '\nwhich rank is correct? (0 for none of the above)\t' ) )
        
        self.beenDrafted( thisRank, 'FA' )
    
    
    #
    #   Replacement Value Calculation
    #
    
    def updateReplacementValue( self ):
        """
        For every player in the draft, calculate their replacement
        value at their position.  We may generalize this
        """
        sortedVals = scipy.sort( self.predictionData, order = [ 'FantasyTeam', 'Pos', 'FantPoints' ] )
        
        replacementValueDic = { sortedVals[ 0 ][ 0 ] : 0.0 }
        
        for i in range( len( sortedVals ) - 1 ):
            rowNow = sortedVals[ i ]
            rowNext = sortedVals[ i + 1 ]
            if rowNow[ 4 ] == rowNext[ 4 ]:
                replacementValueDic[ rowNext[ 0 ] ] = rowNext[ -2 ] - rowNow[ -2 ]
            else:
                replacementValueDic[ rowNext[ 0 ] ] = 0.0
        
        for row in self.predictionData:
            row[ -1 ] = replacementValueDic[ row[0] ]
        
        del replacementValueDic
    
    
    def bestReplacementAvailable(self):
        """
        Calculate the players at each position with the best remaining
        replacement value
        """
        sortedVals = scipy.sort( self.predictionData, order = [ 'FantasyTeam', 'Pos', 'FantPoints' ] )
        
        topNDic = { }
        goneNowDic = { }
        N = 25
        
        for i in range( len( sortedVals ) ):
            
            rowNow = sortedVals[ i ]
            
            if rowNow[ 5 ] == 'FA':
                if  i == len( sortedVals ) - 1:
                    calcNow = True
                else: 
                    rowNext = sortedVals[ i + 1 ]
                
                    if rowNow[ 4 ] != rowNext[ 4 ]:
                        calcNow = True
                    else:
                        calcNow = False
                
                if calcNow:
                    row = list( rowNow )
                    rank, first, last, team, pos, fantTeam = row[ :6 ]
                    points, replVal = row[ -2: ]
                    
                    topNDic[ pos ] = [ row, [] ]
                    
                    for j in range( N ):
                        ind = i - j
                        if ( ind >= 0 ) and ( sortedVals[ ind ][ 4 ] == pos ):
                            topNDic[ pos ][ 1 ].append( sortedVals[ ind ][ -2 ] )
            else:
                row = list( rowNow )
                rank, first, last, team, pos, fantTeam = row[ :6 ]
                points, replVal = row[ -2: ]
                
                if pos not in goneNowDic:
                    goneNowDic[ pos ] = []
                
                goneNowDic[ pos ].append( points )
        
        #
        #   Best available
        #
        
        replacementValueDic = { }
        for ( pos, x ) in topNDic.iteritems():
            row, l = x
            replacementValueDic[ pos ] = [ row, scipy.cumsum( scipy.diff( l ) ) ]
            
        
        self.f1.clf()
        s1 = self.f1.add_subplot( 111 )
        
        for ( pos, x ) in replacementValueDic.iteritems():
            row, l = x
            lab = pos + ' '.join( [','] + row[ 1:3 ] )
            c = POS_COLOR[ pos ]
            s1.plot( l, color = c, marker = 'o', mfc = 'w', mec = c, mew = 2, lw = 2, label = lab )
        
        s1.legend( loc = 'lower left' )
        s1.set_ylim( (-200, 0) )
        s1.set_xlim( (-0.5, 24.5) )
        self.f1.show()
        
        #
        #   How far behind
        #
        self.f2.clf()
        s2 = self.f2.add_subplot( 111 )
        
        isLabel = False
        for ( pos, l ) in goneNowDic.iteritems():
            if pos in replacementValueDic:
                bestPointsLeft = replacementValueDic[ pos ][ 0 ][ -2 ]
                l.reverse()
                pointsLost = scipy.array( l ) - bestPointsLeft
                c = POS_COLOR[ pos ]
                s2.plot( pointsLost, color = c, marker = 'o', mfc = 'w', mec = c, mew = 2, lw = 2, label = pos )
                isLabel = True
                
        if isLabel:
            s2.legend( loc = 'lower left' )
        self.f2.show()
