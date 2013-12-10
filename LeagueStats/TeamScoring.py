########################################################################
#                                                                      #
#   TeamScoring.py                                                     #
#   10/25/2013                                                         #
#                                                                      #
#   Routine to pull the scores from the different matchups... maybe    #
#   other stats.  We'll see!                                           #
#                                                                      #
#                                                                      #
########################################################################

import scipy

import FFFetch


#-----------------------#
#   Module Constants    #
#-----------------------#

#LEAGUE_NAME = 'Sasquatch Nutz'
#LEAGUE_ID   = 209006

FETCHER = FFFetch.FFFetcher()


def getScores():
    """Use the FFFetch object method to get the info, and then build it
    into a dicitonary of for / against score lists

    """
    scores = FETCHER.fetch('schedule', 'seasonScores')
    
    scoreDic = {}
    leagueScoreInfo = {}
    
    for row in scores:
        week, home, away, homeS, awayS = row
        
        if home not in scoreDic:
            scoreDic[home] = {'for': [], 'against': []}
        if away not in scoreDic:
            scoreDic[away] = {'for': [], 'against': []}
        
        scoreDic[home]['for'].append(homeS)
        scoreDic[home]['against'].append(awayS)
        scoreDic[away]['for'].append(awayS)
        scoreDic[away]['against'].append(homeS)
        
        if week not in leagueScoreInfo:
            leagueScoreInfo[week] = {}
            leagueScoreInfo[week]['scores'] = []
        
        leagueScoreInfo[week]['scores'].append(homeS)
    
    #   Week performances
    for week in leagueScoreInfo:
        try:
            leagueScoreInfo[week]['av'] = scipy.average(leagueScoreInfo[week]['scores'])
            leagueScoreInfo[week]['std'] = scipy.std(leagueScoreInfo[week]['scores'])            
        except:
            pass
    
    #   Averages & Stds
    for team in scoreDic:
        #   avs and stds
        try:
            scoreDic[team]['avFor'] = scipy.average(scoreDic[team]['for'])
            scoreDic[team]['avAgainst'] = scipy.average(scoreDic[team]['against'])
            scoreDic[team]['stdFor'] = scipy.std(scoreDic[team]['for'])
            scoreDic[team]['stdAgainst'] = scipy.std(scoreDic[team]['against'])
            
            #   weekly unluckiness
            weekInts = [int(el[el.find(' ') + 1: ]) for el in leagueScoreInfo.keys()]
            maxWeek = max(weekInts) + 1
            weekScoreAvs = scipy.array([leagueScoreInfo['WEEK {}'.format(i)]['av'] for i in range(1, maxWeek)])
            
            #   difs
            scoreDic[team]['difFor'] = scipy.array(scoreDic[team]['for']) - weekScoreAvs
            scoreDic[team]['difAgainst'] = scipy.array(scoreDic[team]['against']) - weekScoreAvs
        except:
            pass
        
    return scoreDic, leagueScoreInfo
    