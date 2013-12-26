###############################################################################
#                                                                             #
#   TeamScoring.py                                                            #
#   10/25/2013                                                                #
#                                                                             #
#   Routine to pull the scores from the different matchups... maybe           #
#   other stats.  We'll see!                                                  #
#                                                                             #
#                                                                             #
###############################################################################

import os
import pylab
import scipy

import FFFetch


#-----------------------#
#   Module Constants    #
#-----------------------#

#LEAGUE_NAME = 'Sasquatch Nutz'
#LEAGUE_ID   = 209006

FETCHER = FFFetch.FFFetcher()

PLOT_DIR = './plots'
if not os.path.isdir(PLOT_DIR):
    os.mkdir(PLOT_DIR)


#-----------------------#
#   Main routines       #
#-----------------------#

def get_scores():
    """Use the FFFetch object method to get the info, and then build it
    into a dicitonary of for / against score lists

    """
    scores = FETCHER.fetch('schedule', 'seasonScores')

    scoreDic = {}
    leagueScoreInfo = {}

    for row in scores:
        week, home, away, homeS, awayS = row

        if homeS == 'Box':
            break
        else:
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
            weekInts = [int(el[el.find(' ') + 1:]) for el in leagueScoreInfo.keys()]
            maxWeek = max(weekInts) + 1
            weekScoreAvs = scipy.array([leagueScoreInfo['WEEK {}'.format(i)]['av'] for i in range(1, maxWeek)])

            #   difs
            scoreDic[team]['difFor'] = scipy.array(scoreDic[team]['for']) - weekScoreAvs
            scoreDic[team]['difAgainst'] = scipy.array(scoreDic[team]['against']) - weekScoreAvs
        except:
            pass

    return scoreDic, leagueScoreInfo


def make_all_plots(save=True):
    """Write every plot and save it to file

    """
    scoreDic, leagueScoreInfo = get_scores()

    plot_against(save=True, sd=scoreDic, lsi=leagueScoreInfo)
    plot_for(save=True, sd=scoreDic, lsi=leagueScoreInfo)
    plot_dif_against(save=True, sd=scoreDic, lsi=leagueScoreInfo)
    plot_dif_for(save=True, sd=scoreDic, lsi=leagueScoreInfo)


def plot_against(save, sd, lsi):
    """
    """
    f = pylab.figure()
    s = f.add_subplot(111)

    for team, teamScores in sd.iteritems():
        teamAgainst = scipy.array(teamScores['against'])
        teamAgainst /= scipy.array([lsi[w]['av'] for w in sorted(lsi.keys())])
        s.plot(teamAgainst, lw=2, ls='--', label=team)

    s.legend()

    if save:
        f.savefig(os.path.join(PLOT_DIR, 'against.png'), dpi=300)

def plot_for(save, sd, lsi):
    """
    """
    f = pylab.figure()
    s = f.add_subplot(111)

    for team, teamScores in sd.iteritems():
        teamFor = scipy.array(teamScores['for'])
        teamFor /= scipy.array([lsi[w]['av'] for w in sorted(lsi.keys())])
        s.plot(teamFor, lw=2, ls='--', label=team)

    s.legend()

    if save:
        f.savefig(os.path.join(PLOT_DIR, 'for.png'), dpi=300)


def plot_dif_against(save, sd, lsi):
    """
    """
    f = pylab.figure()
    s = f.add_subplot(111)

    for team, teamScores in sd.iteritems():
        teamAgainst = scipy.array(teamScores['difAgainst'])
        teamAgainst /= scipy.array([lsi[w]['av'] for w in sorted(lsi.keys())])
        s.plot(teamAgainst, lw=2, ls='--', label=team)

    s.legend()

    if save:
        f.savefig(os.path.join(PLOT_DIR, 'difAgainst.png'), dpi=300)


def plot_dif_for(save, sd, lsi):
    """
    """
    f = pylab.figure()
    s = f.add_subplot(111)

    for team, teamScores in sd.iteritems():
        teamFor = scipy.array(teamScores['difFor'])
        teamFor /= scipy.array([lsi[w]['av'] for w in sorted(lsi.keys())])
        s.plot(teamFor, lw=2, ls='--', label=team)

    s.legend()

    if save:
        f.savefig(os.path.join(PLOT_DIR, 'difFor.png'), dpi=300)
